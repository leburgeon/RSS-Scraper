"""Tests for mention volume metric calculation."""

import pandas as pd

from metrics import (
    create_empty_dataframe,
    filter_company_rows,
    compute_mention_volume,)


def sample_mentions_dataframe():
    """Create a simple dataframe for testing."""
    data = [
        {
            "entity_id": "1",
            "entity_name": "Apple",
            "entity_type": "company",
            "article_id": "a1",
            "sentiment": "positive",
            "mention_count": 3
        },
        {
            "entity_id": "1",
            "entity_name": "Apple",
            "entity_type": "company",
            "article_id": "a2",
            "sentiment": "negative",
            "mention_count": 2
        },
        {
            "entity_id": "1",
            "entity_name": "Apple",
            "entity_type": "company",
            "article_id": "a2",
            "sentiment": "negative",
            "mention_count": 2
        },
        {
            "entity_id": "2",
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_id": "a1",
            "sentiment": "neutral",
            "mention_count": 1
        },
        {
            "entity_id": "2",
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_id": "a3",
            "sentiment": "positive",
            "mention_count": 4
        },
        {
            "entity_id": "3",
            "entity_name": "Rishi Sunak",
            "entity_type": "person",
            "article_id": "a4",
            "sentiment": "positive",
            "mention_count": 5
        }
    ]

    return pd.DataFrame(data)


def test_create_empty_dataframe():
    """Test creating an empty dataframe with specified columns."""
    columns = ["a", "b", "c"]
    df = create_empty_dataframe(columns)

    assert df.empty
    assert list(df.columns) == columns


def test_filter_company_rows_only_keeps_companies():
    """Test that filtering for company rows only keeps those rows."""
    df = sample_mentions_dataframe()
    filtered_df = filter_company_rows(
        df,
        ["entity_id", "entity_name", "entity_type", "article_id"],
        "Testing filter"
    )

    assert len(filtered_df) == 5
    assert all(filtered_df["entity_type"] == "company")


def test_compute_mention_volume():
    """Test that mention volume is computed correctly."""
    df = sample_mentions_dataframe()
    result_df = compute_mention_volume(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    # Apple appears in a1 and a2 only, so distinct article count = 2
    assert apple_row["mention_volume"] == 2

    # Tesla appears in a1 and a3, so distinct article count = 2
    assert tesla_row["mention_volume"] == 2


def test_compute_mention_volume_empty_dataframe():
    """Test that computing mention volume on an empty dataframe returns an empty dataframe."""
    empty_df = pd.DataFrame(
        columns=["entity_id", "entity_name", "entity_type", "article_id"]
    )

    result_df = compute_mention_volume(empty_df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_id", "entity_name", "entity_type", "mention_volume"
    ]
