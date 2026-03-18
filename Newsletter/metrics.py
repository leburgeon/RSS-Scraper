"""This script will be used to define the metrics for the newsletter report,

These will accquired by connecting to dynamoDB and running queries to get the relevant data for the newsletter report.

1)Mention Volume:

count(distinct article_id) where entity_id = X

2)Sentiment Distribution:
For each company in date range:

(pos/neu/neg mention)/articles

3)Share of Voice:
For each company in date range:

SOV= company article count/total article count
"""


import logging
from datetime import datetime, timedelta

import boto3
import pandas as pd
from boto3.dynamodb.conditions import Key


logging.basicConfig(level=logging.INFO)


def get_yesterday_date():
    """Return yesterday's date as YYYY-MM-DD."""
    yesterday = datetime.utcnow().date() - timedelta(days=1)
    return str(yesterday)


def get_dynamodb_table(table_name, region_name):
    """Connect to DynamoDB and return the table."""
    logging.info("Connecting to DynamoDB table")
    dynamodb = boto3.resource("dynamodb", region_name=region_name)
    table = dynamodb.Table(table_name)
    return table


def get_mention_items_for_date(table, article_date):
    """Retrieve all mention items for one date."""
    logging.info("Retrieving mention items for %s", article_date)

    all_items = []

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

    logging.info("Retrieved %s mention items", len(all_items))
    return all_items


def create_mentions_dataframe(items):
    """Convert retrieved items into a pandas DataFrame."""
    logging.info("Creating DataFrame")
    df = pd.DataFrame(items)
    logging.info("DataFrame has %s rows", len(df))
    return df


def compute_mention_volume(df):
    """
    Compute mention volume for companies.

    Mention volume = number of distinct articles each company
    appears in for the day.
    """
    logging.info("Computing mention volume")

    company_df = df[df["entity_type"] == "company"].copy()

    company_df = company_df[
        ["entity_id", "entity_name", "entity_type", "article_id"]
    ].dropna()

    company_df = company_df.drop_duplicates(subset=["entity_id", "article_id"])

    mention_volume_df = (
        company_df.groupby(
            ["entity_id", "entity_name", "entity_type"],
            as_index=False
        )
        .agg(mention_volume=("article_id", "count"))
        .sort_values(by="mention_volume", ascending=False)
        .reset_index(drop=True)
    )

    logging.info("Computed mention volume for %s companies",
                 len(mention_volume_df))
    return mention_volume_df


def get_top_3_companies(mention_volume_df):
    """Return top 3 companies by mention volume."""
    return mention_volume_df.head(3).copy()


def get_bottom_3_companies(mention_volume_df):
    """Return bottom 3 companies by mention volume, excluding zero."""
    non_zero_df = mention_volume_df[mention_volume_df["mention_volume"] > 0].copy(
    )
    non_zero_df = non_zero_df.sort_values(by="mention_volume", ascending=True)
    return non_zero_df.head(3).copy()

# Sentiment function


logging.basicConfig(level=logging.INFO)


def filter_company_sentiment_rows(df):
    """Keep only company rows with the columns needed for sentiment analysis."""
    logging.info("Filtering company sentiment rows")

    company_df = df[df["entity_type"] == "company"].copy()
    company_df = company_df[
        ["entity_id", "entity_name", "entity_type", "sentiment"]
    ].dropna()

    return company_df


def count_sentiment_by_company(company_df):
    """Count positive, neutral, and negative rows for each company."""
    logging.info("Counting sentiment by company")

    sentiment_counts_df = (
        company_df.groupby(
            ["entity_id", "entity_name", "entity_type", "sentiment"]
        )
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )

    for sentiment_name in ["positive", "neutral", "negative"]:
        if sentiment_name not in sentiment_counts_df.columns:
            sentiment_counts_df[sentiment_name] = 0

    return sentiment_counts_df


def add_sentiment_percentages(sentiment_counts_df):
    """Add total, positive_pct, neutral_pct, and negative_pct columns."""
    logging.info("Adding sentiment percentages")

    sentiment_counts_df["total"] = (
        sentiment_counts_df["positive"]
        + sentiment_counts_df["neutral"]
        + sentiment_counts_df["negative"]
    )

    sentiment_counts_df["positive_pct"] = (
        sentiment_counts_df["positive"] / sentiment_counts_df["total"]
    )
    sentiment_counts_df["neutral_pct"] = (
        sentiment_counts_df["neutral"] / sentiment_counts_df["total"]
    )
    sentiment_counts_df["negative_pct"] = (
        sentiment_counts_df["negative"] / sentiment_counts_df["total"]
    )

    return sentiment_counts_df


def compute_sentiment_distribution(df):
    """
    Compute sentiment counts and percentages for each company.

    Expected columns:
    - entity_id
    - entity_name
    - entity_type
    - sentiment
    """
    logging.info("Computing sentiment distribution")

    company_df = filter_company_sentiment_rows(df)
    sentiment_counts_df = count_sentiment_by_company(company_df)
    sentiment_distribution_df = add_sentiment_percentages(sentiment_counts_df)

    sentiment_distribution_df = sentiment_distribution_df.sort_values(
        by="positive_pct",
        ascending=False
    ).reset_index(drop=True)

    logging.info(
        "Computed sentiment distribution for %s companies",
        len(sentiment_distribution_df)
    )
    return sentiment_distribution_df


def main():
    table_name = "c22_charlie_media_mvp"
    region_name = "eu-west-2"

    article_date = get_yesterday_date()

    table = get_dynamodb_table(table_name, region_name)
    items = get_mention_items_for_date(table, article_date)

    if not items:
        logging.info("No mention items found for yesterday")
        return

    df = create_mentions_dataframe(items)
    mention_volume_df = compute_mention_volume(df)

    top_3_companies = get_top_3_companies(mention_volume_df)
    bottom_3_companies = get_bottom_3_companies(mention_volume_df)

    print("\nTop 3 Companies by Mention Volume")
    print(top_3_companies)

    print("\nBottom 3 Companies by Mention Volume")
    print(bottom_3_companies)

    print("\nMention Volume Results")
    print(mention_volume_df)


if __name__ == "__main__":
    main()
