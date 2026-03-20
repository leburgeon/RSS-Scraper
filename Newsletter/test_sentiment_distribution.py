"""Tests for sentiment distribution calculation and related functions."""

import pandas as pd

from metrics import (
    filter_company_sentiment_rows,
    count_sentiment_by_company,
    sentiment_distribution_calculate,
    top_3_rows,
)


def sample_sentiment_df():
    """Create a simple dataframe for sentiment tests."""
    data = [
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a1",
            "sentiment": "positive",
            "mention_count": 2,
        },
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a2",
            "sentiment": "positive",
            "mention_count": 1,
        },
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a3",
            "sentiment": "negative",
            "mention_count": 1,
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a4",
            "sentiment": "negative",
            "mention_count": 3,
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a5",
            "sentiment": "negative",
            "mention_count": 2,
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a6",
            "sentiment": "neutral",
            "mention_count": 1,
        },
        {
            "entity_name": "Meta",
            "entity_type": "company",
            "article_guid": "a7",
            "sentiment": "neutral",
            "mention_count": 2,
        },
        {
            "entity_name": "Meta",
            "entity_type": "company",
            "article_guid": "a8",
            "sentiment": "unknown",
            "mention_count": 1,
        },
        {
            "entity_name": "Guardian",
            "entity_type": "company",
            "article_guid": "a9",
            "sentiment": "positive",
            "mention_count": 1,
        },
        {
            "entity_name": "Sundar Pichai",
            "entity_type": "person",
            "article_guid": "a10",
            "sentiment": "positive",
            "mention_count": 1,
        },
    ]
    return pd.DataFrame(data)


def test_filter_company_sentiment_rows_keeps_only_needed_columns():
    """Test that filter_company_sentiment_rows returns a dataframe with only the
    needed columns and only company rows."""

    df = sample_sentiment_df()

    result_df = filter_company_sentiment_rows(df)

    assert list(result_df.columns) == [
        "entity_name", "entity_type", "sentiment"]
    assert all(result_df["entity_type"] == "company")


def test_filter_company_sentiment_rows_excludes_guardian_and_non_company():
    """Test that filter_company_sentiment_rows excludes rows for Guardian and non-company entities."""

    df = sample_sentiment_df()

    result_df = filter_company_sentiment_rows(df)

    names = result_df["entity_name"].tolist()

    assert "Guardian" not in names
    assert "Sundar Pichai" not in names


def test_count_sentiment_by_company_counts_positive_neutral_negative():
    """Test that count_sentiment_by_company counts the number of 
    positive, neutral, and negative sentiments correctly for each company."""

    df = sample_sentiment_df()
    filtered_df = filter_company_sentiment_rows(df)

    result_df = count_sentiment_by_company(filtered_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["positive"] == 2
    assert apple_row["negative"] == 1
    assert apple_row["neutral"] == 0

    assert tesla_row["positive"] == 0
    assert tesla_row["negative"] == 2
    assert tesla_row["neutral"] == 1


def test_count_sentiment_by_company_ignores_unknown_sentiment_values():
    """Test that count_sentiment_by_company ignores sentiment
      values that are not positive, neutral, or negative."""

    df = sample_sentiment_df()
    filtered_df = filter_company_sentiment_rows(df)

    result_df = count_sentiment_by_company(filtered_df)

    meta_row = result_df[result_df["entity_name"] == "Meta"].iloc[0]

    assert meta_row["neutral"] == 1
    assert meta_row["positive"] == 0
    assert meta_row["negative"] == 0


def test_count_sentiment_by_company_returns_all_sentiment_columns():
    """Test that count_sentiment_by_company returns a dataframe with columns for
    positive, neutral, and negative sentiment counts."""

    df = pd.DataFrame([
        {"entity_name": "Apple", "entity_type": "company", "sentiment": "positive"}
    ])

    result_df = count_sentiment_by_company(df)

    assert "positive" in result_df.columns
    assert "neutral" in result_df.columns
    assert "negative" in result_df.columns


def test_sentiment_distribution_calculate_returns_empty_dataframe_for_empty_input():
    """Test that sentiment_distribution_calculate returns an empty dataframe
    with the expected columns when given an empty dataframe."""

    df = pd.DataFrame(columns=["entity_name", "entity_type", "sentiment"])

    result_df = sentiment_distribution_calculate(df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type", "positive", "neutral", "negative"
    ]


def test_sentiment_distribution_calculate_returns_expected_counts():
    """Test that sentiment_distribution_calculate returns the expected counts of
    positive, neutral, and negative sentiments for each company."""

    df = sample_sentiment_df()

    result_df = sentiment_distribution_calculate(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]

    assert apple_row["positive"] == 2
    assert apple_row["neutral"] == 0
    assert apple_row["negative"] == 1


def test_top_3_rows_for_positive_sentiment_returns_highest_positive_counts():
    """Test that top_3_rows returns the 3 rows with the highest positive sentiment counts."""

    df = sample_sentiment_df()
    sentiment_df = sentiment_distribution_calculate(df)

    result_df = top_3_rows(sentiment_df, "positive")

    assert len(result_df) <= 3
    assert result_df.iloc[0]["entity_name"] == "Apple"
