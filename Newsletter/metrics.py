"""This script will be used to define the metrics for the newsletter report,

These will accquired by connecting to dynamoDB and running
queries to get the relevant data for the newsletter report.

1)Mention Volume:

count(distinct article_guid) where entity_id = X

2)Sentiment Distribution:
For each company in date range:

(pos/neu/neg mention)/articles

3)Share of Voice:
For each company in date range:

SOV= company article count/total articles
"""

# article id can be replaced for article_guid
# entity id is replaced for entity_name


from botocore.exceptions import BotoCoreError, ClientError
import logging
from datetime import datetime, timedelta

import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, BotoCoreError


logging.basicConfig(level=logging.INFO)


def yesterday_date():
    """Return yesterday's date as YYYY-MM-DD."""
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    return str(yesterday)


def retrieve_dynamodb_table(table_name: str, region_name: str):
    """Connect to DynamoDB and return the table."""
    try:
        logging.info(
            "Connecting to DynamoDB table: %s in region: %s",
            table_name,
            region_name
        )

        dynamodb = boto3.resource("dynamodb", region_name=region_name)
        table = dynamodb.Table(table_name)

        logging.info("Successfully connected to DynamoDB table")
        return table

    except ClientError as error:
        logging.error(
            "DynamoDB client error while connecting to table: %s", error)
        raise

    except BotoCoreError as error:
        logging.error(
            "Boto core error while connecting to DynamoDB: %s", error)
        raise


def mention_items_for_date(table, article_date: str) -> list:
    """Retrieve all mention items for one date."""
    logging.info("Retrieving mention items for %s", article_date)

    all_items = []

    try:
        response = table.query(
            KeyConditionExpression=Key("PK").eq(f"MENTION_DATE#{article_date}")
        )
        all_items.extend(response.get("Items", []))

        while "LastEvaluatedKey" in response:
            response = table.query(
                KeyConditionExpression=Key("PK").eq(
                    f"MENTION_DATE#{article_date}"),
                ExclusiveStartKey=response["LastEvaluatedKey"]
            )
            all_items.extend(response.get("Items", []))

    except ClientError as error:
        logging.error(
            "DynamoDB client error retrieving mention items: %s", error)
        raise

    except BotoCoreError as error:
        logging.error("Boto core error retrieving mention items: %s", error)
        raise

    logging.info("Retrieved %s mention items", len(all_items))
    return all_items


def mentions_dataframe_creation(items: list) -> pd.DataFrame:
    """Convert retrieved items into a pandas DataFrame."""
    logging.info("Creating DataFrame")
    df = pd.DataFrame(items)
    logging.info("DataFrame has %s rows", len(df))
    return df


def filter_company_rows(df: pd.DataFrame, required_columns: list, log_message: str) -> pd.DataFrame:
    """Keep only company rows with the required columns."""
    logging.info(log_message)

    # and "people" is also a type of entity to be added
    company_df = df[(df["entity_type"] == "company") |
                    (df["entity_type"] == "people")].copy()

    if company_df.empty:
        return pd.DataFrame(columns=required_columns)

    company_df = company_df[required_columns].dropna()

    return company_df


def compute_mention_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute mention volume for companies.
    Mention volume = number of distinct articles each company
    appears in for the day.
    """
    logging.info("Computing mention volume")

    output_columns = ["entity_name",
                      "entity_type", "mention_volume"]

    required_columns = ["entity_name", "entity_type", "article_guid"]

    company_df = filter_company_rows(
        df, required_columns, "Filtering company rows for mention volume")

    if company_df.empty:
        return pd.DataFrame(columns=output_columns)

    mention_volume_df = (
        company_df.groupby(["entity_name", "entity_type"],
                           as_index=False
                           )
        .agg(mention_volume=("article_guid", "count"))
        .sort_values(by="mention_volume", ascending=False)
        .reset_index(drop=True)
    )

    logging.info("Computed mention volume for %s companies",
                 len(mention_volume_df))
    return mention_volume_df


def filter_company_sentiment_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only company rows with the columns needed for sentiment analysis."""
    required_columns = ["entity_name", "entity_type", "sentiment"]

    return filter_company_rows(df, required_columns, "Filtering company sentiment rows")


def count_sentiment_by_company(company_df: pd.DataFrame) -> pd.DataFrame:
    """Count positive, neutral, and negative rows for each company."""

    logging.info("Counting sentiment by company")

    output_columns = ["entity_name", "entity_type",
                      "positive", "neutral", "negative"]

    if company_df.empty:
        return pd.DataFrame(columns=output_columns)

    sentiment_counts_df = (
        company_df.groupby(
            ["entity_name", "entity_type", "sentiment"]
        )
        .size()
        # unstack may not be needed as data will be cleaned
        .unstack(fill_value=0)
        .reset_index()
    )

    sentiment_counts_df.columns.name = None

    sentiment_names = ["positive", "neutral", "negative"]

    for sentiment_name in sentiment_names:
        if sentiment_name not in sentiment_counts_df.columns:
            sentiment_counts_df[sentiment_name] = 0

    return sentiment_counts_df


def sentiment_percentages(sentiment_counts_df: pd.DataFrame) -> pd.DataFrame:
    """Add total, positive_pct, neutral_pct, and negative_pct columns."""
    logging.info("Adding sentiment percentages")

    output_columns = ["entity_name", "entity_type",
                      "positive", "neutral", "negative",
                      "total", "positive_pct", "neutral_pct", "negative_pct"
                      ]

    if sentiment_counts_df.empty:
        return pd.DataFrame(columns=output_columns)

    sentiment_counts_df["total"] = (
        sentiment_counts_df["positive"]
        + sentiment_counts_df["neutral"]
        + sentiment_counts_df["negative"]
    )

    sentiment_counts_df["positive_pct"] = 0.0
    sentiment_counts_df["neutral_pct"] = 0.0
    sentiment_counts_df["negative_pct"] = 0.0

    # none zero mask to avoid division by zero
    non_zero = sentiment_counts_df["total"] > 0

    sentiment_counts_df.loc[non_zero, "positive_pct"] = (
        sentiment_counts_df.loc[non_zero, "positive"]
        / sentiment_counts_df.loc[non_zero, "total"]
    )

    sentiment_counts_df.loc[non_zero, "neutral_pct"] = (
        sentiment_counts_df.loc[non_zero, "neutral"]
        / sentiment_counts_df.loc[non_zero, "total"]
    )

    sentiment_counts_df.loc[non_zero, "negative_pct"] = (
        sentiment_counts_df.loc[non_zero, "negative"]
        / sentiment_counts_df.loc[non_zero, "total"]
    )

    return sentiment_counts_df


def sentiment_distribution_calculate(df: pd.DataFrame) -> pd.DataFrame:
    """Compute sentiment counts and percentages for each company.
    - positive_pct for top 3 positive sentiment
    - negative_pct for top 3 negative sentiment"""

    logging.info("Computing sentiment distribution")

    output_columns = ["entity_name", "entity_type",
                      "positive", "neutral", "negative",
                      "total", "positive_pct", "neutral_pct", "negative_pct"
                      ]

    company_df = filter_company_sentiment_rows(df)

    if company_df.empty:
        return pd.DataFrame(columns=output_columns)

    sentiment_counts_df = count_sentiment_by_company(company_df)
    sentiment_distribution_df = sentiment_percentages(sentiment_counts_df)
    sentiment_distribution_df = sentiment_distribution_df.reset_index(
        drop=True)

    logging.info("Computed sentiment distribution for %s companies",
                 len(sentiment_distribution_df))

    return sentiment_distribution_df


def filter_company_article_rows(df: pd.DataFrame) -> pd.DataFrame:
    """Keep only company rows and the columns needed for share of voice."""

    required_columns = ["entity_name", "entity_type",
                        "article_guid", "mention_count"]

    return filter_company_rows(df, required_columns, "Filtering company rows for share of voice")


def articles_by_company_count(company_df: pd.DataFrame) -> pd.DataFrame:
    """Summing total mentions across all articles for each company 
    to get article count for share of voice calculation."""

    logging.info("Counting total mentions by company")

    output_columns = ["entity_name", "entity_type", "article_count"]

    if company_df.empty:
        return pd.DataFrame(columns=output_columns)

    article_counts_df = (
        company_df.groupby(
            ["entity_name", "entity_type"],
            as_index=False
        )
        .agg(article_count=("mention_count", "sum"))
    )

    return article_counts_df


def add_share_of_voice(article_counts_df: pd.DataFrame) -> pd.DataFrame:
    """share_of_voice function to compute total mentions across all articles
    as companies can be mentioned multiple times in same article"""
    logging.info("Adding share of voice")

    output_columns = [
        "entity_name", "entity_type",
        "article_count", "share_of_voice"
    ]

    if article_counts_df.empty:
        return pd.DataFrame(columns=output_columns)

    total_article_mentions = article_counts_df["article_count"].sum()

    if total_article_mentions == 0:
        article_counts_df["share_of_voice"] = 0.0
    else:
        article_counts_df["share_of_voice"] = (
            article_counts_df["article_count"] / total_article_mentions
        )

    return article_counts_df


def share_of_voice_calculate(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute share of voice for each company.
    share_of_voice =
    company total mention_count / total mention_count across all companies
    """
    logging.info("Computing share of voice")

    output_columns = [
        "entity_name", "entity_type",
        "article_count", "share_of_voice"
    ]

    company_df = filter_company_article_rows(df)

    if company_df.empty:
        return pd.DataFrame(columns=output_columns)

    article_counts_df = articles_by_company_count(company_df)
    share_of_voice_df = add_share_of_voice(article_counts_df)

    share_of_voice_df = share_of_voice_df.sort_values(
        by="share_of_voice",
        ascending=False
    ).reset_index(drop=True)

    logging.info("Computed share of voice for %s companies",
                 len(share_of_voice_df))
    return share_of_voice_df


def top_3_rows(df: pd.DataFrame, metric_column: str) -> pd.DataFrame:
    """Return top 3 rows by the chosen metric column."""
    if df.empty:
        return df.copy()

    top_3_df = df.sort_values(by=metric_column, ascending=False).head(3).copy()
    return top_3_df


def bottom_3_rows(df: pd.DataFrame, metric_column: str) -> pd.DataFrame:
    """Return bottom 3 rows by the chosen metric column, excluding zero."""
    if df.empty:
        return df.copy()

    non_zero_df = df[df[metric_column] > 0].copy()

    if non_zero_df.empty:
        return non_zero_df.copy()

    bottom_3_df = non_zero_df.sort_values(
        by=metric_column, ascending=True).head(3).copy()
    return bottom_3_df


def main():
    """Main function to run the metrics calculations and print results."""

    table_name = "c22_charlie_media_mvp"
    region_name = "eu-west-2"

    article_date = yesterday_date()

    table = retrieve_dynamodb_table(table_name, region_name)
    items = mention_items_for_date(table, article_date)

    if not items:
        logging.info("No mention items found for yesterday")
        return

    df = mentions_dataframe_creation(items)

    mention_volume_df = compute_mention_volume(df)
    sentiment_distribution_df = sentiment_distribution_calculate(df)
    share_of_voice_df = share_of_voice_calculate(df)

    top_3_companies = top_3_rows(mention_volume_df, "mention_volume")
    bottom_3_companies = bottom_3_rows(mention_volume_df, "mention_volume")

    top_3_sentiment_companies = top_3_rows(
        sentiment_distribution_df,
        "positive_pct"
    )

    bottom_3_sentiment_companies = top_3_rows(
        sentiment_distribution_df,
        "negative_pct"
    )

    top_3_share_of_voice_companies = top_3_rows(
        share_of_voice_df,
        "share_of_voice"
    )

    bottom_3_share_of_voice_companies = bottom_3_rows(
        share_of_voice_df,
        "share_of_voice"
    )

    print("\nTop 3 Companies by Mention Volume")
    print(top_3_companies)

    print("\nBottom 3 Companies by Mention Volume")
    print(bottom_3_companies)

    print("\nTop 3 Companies by Positive Sentiment Percentage")
    print(top_3_sentiment_companies)

    print("\nTop 3 Companies by Negative Sentiment Percentage")
    print(bottom_3_sentiment_companies)

    print("\nTop 3 Companies by Share of Voice")
    print(top_3_share_of_voice_companies)

    print("\nBottom 3 Companies by Share of Voice")
    print(bottom_3_share_of_voice_companies)


if __name__ == "__main__":
    main()
