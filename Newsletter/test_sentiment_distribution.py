"""Tests for sentiment distribution metric calculation."""

import pandas as pd

from test_mention_volume import sample_mentions_dataframe

from metrics import (
    filter_company_sentiment_rows,
    count_sentiment_by_company,
    sentiment_percentages,
    sentiment_distribution_calculate,)


def test_filter_company_sentiment_rows():
    """Filtering for company sentiment rows only keeps those rows."""
    df = sample_mentions_dataframe()
    result_df = filter_company_sentiment_rows(df)

    assert len(result_df) == 5
    assert "sentiment" in result_df.columns
    assert all(result_df["entity_type"] == "company")


def test_count_sentiment_by_company():
    """Test that sentiment counts are computed correctly by company."""
    df = sample_mentions_dataframe()
    company_df = filter_company_sentiment_rows(df)
    result_df = count_sentiment_by_company(company_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["positive"] == 1
    assert apple_row["negative"] == 1
    assert apple_row["neutral"] == 0

    assert tesla_row["positive"] == 1
    assert tesla_row["neutral"] == 1
    assert tesla_row["negative"] == 0


def test_sentiment_percentages():
    """Test that sentiment percentages are calculated correctly."""
    sentiment_counts_df = pd.DataFrame([
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "positive": 1,
            "neutral": 1,
            "negative": 2
        }
    ])

    result_df = sentiment_percentages(sentiment_counts_df)
    row = result_df.iloc[0]

    assert row["total"] == 4
    assert row["positive_pct"] == 1 / 4
    assert row["neutral_pct"] == 1 / 4
    assert row["negative_pct"] == 2 / 4


def test_sentiment_distribution_calculate():
    """Test that sentiment distribution is calculated correctly."""
    df = sample_mentions_dataframe()
    result_df = sentiment_distribution_calculate(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]

    assert apple_row["total"] == 2
    assert apple_row["positive"] == 1
    assert apple_row["negative"] == 1
    assert apple_row["positive_pct"] == 1 / 2
    assert apple_row["negative_pct"] == 1 / 2


def test_sentiment_distribution_empty_dataframe():
    """Test that calculating sentiment distribution on 
    an empty dataframe returns an empty dataframe."""

    empty_df = pd.DataFrame(
        columns=["entity_name", "entity_type", "sentiment"]
    )

    result_df = sentiment_distribution_calculate(empty_df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type",
        "positive", "neutral", "negative",
        "total", "positive_pct", "neutral_pct", "negative_pct"
    ]
