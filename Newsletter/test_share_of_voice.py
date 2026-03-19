"""Tests for share of voice calculation and related functions."""

import pandas as pd

from metrics import (
    filter_company_article_rows,
    articles_by_company_count,
    add_share_of_voice,
    share_of_voice_calculate,
    top_3_rows,
    bottom_3_rows,
)


def sample_share_of_voice_df():
    """Create a simple dataframe for share of voice tests."""
    data = [
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a1",
            "mention_count": 4,
            "sentiment": "positive",
        },
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a2",
            "mention_count": 2,
            "sentiment": "neutral",
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a3",
            "mention_count": 3,
            "sentiment": "negative",
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a4",
            "mention_count": 1,
            "sentiment": "positive",
        },
        {
            "entity_name": "Meta",
            "entity_type": "company",
            "article_guid": "a5",
            "mention_count": 2,
            "sentiment": "neutral",
        },
        {
            "entity_name": "Guardian",
            "entity_type": "company",
            "article_guid": "a6",
            "mention_count": 10,
            "sentiment": "positive",
        },
        {
            "entity_name": "Jane Doe",
            "entity_type": "person",
            "article_guid": "a7",
            "mention_count": 5,
            "sentiment": "positive",
        },
    ]
    return pd.DataFrame(data)


def test_filter_company_article_rows_keeps_only_needed_columns():
    """Test that filtering for company article rows keeps 
    only the needed columns and excludes non-company rows."""

    df = sample_share_of_voice_df()

    result_df = filter_company_article_rows(df)

    assert list(result_df.columns) == [
        "entity_name", "entity_type", "article_guid", "mention_count"
    ]
    assert all(result_df["entity_type"] == "company")


def test_filter_company_article_rows_excludes_guardian_and_non_company():
    """Test that filtering for company article rows excludes
      rows for Guardian and non-company entities."""

    df = sample_share_of_voice_df()

    result_df = filter_company_article_rows(df)

    names = result_df["entity_name"].tolist()

    assert "Guardian" not in names
    assert "Jane Doe" not in names


def test_articles_by_company_count_sums_mention_count_correctly():
    """Test that articles_by_company_count sums the
      mention_count correctly to get article_count per company."""

    df = sample_share_of_voice_df()
    filtered_df = filter_company_article_rows(df)

    result_df = articles_by_company_count(filtered_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["article_count"] == 6
    assert tesla_row["article_count"] == 4


def test_add_share_of_voice_calculates_fraction_correctly():
    """Test that add_share_of_voice calculates the share of voice
      as the fraction of article_count over total article_count."""

    article_counts_df = pd.DataFrame([
        {"entity_name": "Apple", "entity_type": "company", "article_count": 6},
        {"entity_name": "Tesla", "entity_type": "company", "article_count": 4},
    ])

    result_df = add_share_of_voice(article_counts_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["share_of_voice"] == 0.6
    assert tesla_row["share_of_voice"] == 0.4


def test_add_share_of_voice_returns_zero_when_total_is_zero():
    """Test that add_share_of_voice returns a share of voice of 0.0 for all rows
      when the total article_count is zero to avoid division by zero."""

    article_counts_df = pd.DataFrame([
        {"entity_name": "Apple", "entity_type": "company", "article_count": 0},
        {"entity_name": "Tesla", "entity_type": "company", "article_count": 0},
    ])

    result_df = add_share_of_voice(article_counts_df)

    assert all(result_df["share_of_voice"] == 0.0)


def test_share_of_voice_calculate_returns_expected_values():
    """Test that share_of_voice_calculate returns the 
    expected article counts and share of voice values."""

    df = sample_share_of_voice_df()

    result_df = share_of_voice_calculate(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]
    meta_row = result_df[result_df["entity_name"] == "Meta"].iloc[0]

    total_mentions = 6 + 4 + 2

    assert apple_row["article_count"] == 6
    assert tesla_row["article_count"] == 4
    assert meta_row["article_count"] == 2
    assert apple_row["share_of_voice"] == 6 / total_mentions
    assert tesla_row["share_of_voice"] == 4 / total_mentions
    assert meta_row["share_of_voice"] == 2 / total_mentions


def test_share_of_voice_calculate_returns_empty_dataframe_for_empty_input():
    """Test that share_of_voice_calculate returns an empty dataframe 
    with the expected columns when given an empty dataframe."""

    df = pd.DataFrame(columns=[
        "entity_name", "entity_type", "article_guid", "mention_count"
    ])

    result_df = share_of_voice_calculate(df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type", "article_count", "share_of_voice"
    ]


def test_top_and_bottom_rows_work_for_share_of_voice():
    """Test that top_3_rows and bottom_3_rows return 
    the correct rows based on share of voice values."""

    df = sample_share_of_voice_df()
    share_of_voice_df = share_of_voice_calculate(df)

    top_df = top_3_rows(share_of_voice_df, "share_of_voice")
    bottom_df = bottom_3_rows(share_of_voice_df, "share_of_voice")

    assert len(top_df) <= 3
    assert len(bottom_df) <= 3
    assert top_df.iloc[0]["share_of_voice"] >= top_df.iloc[-1]["share_of_voice"]
    assert bottom_df.iloc[0]["share_of_voice"] <= bottom_df.iloc[-1]["share_of_voice"]
