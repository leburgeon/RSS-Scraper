"""Tests for share of voice calculation 
functions and top and bottom 3 rows functions."""


import pandas as pd

from test_mention_volume import sample_mentions_dataframe
from metrics import (
    filter_company_article_rows,
    articles_by_company_count,
    add_share_of_voice,
    share_of_voice_calculate,
    top_3_rows,
    bottom_3_rows
)


def test_filter_company_article_rows():
    """Test that filtering for company article rows only keeps those rows."""

    df = sample_mentions_dataframe()
    result_df = filter_company_article_rows(df)

    assert len(result_df) == 5
    assert "mention_count" in result_df.columns
    assert all(result_df["entity_type"] == "company")


def test_articles_by_company_count():
    """Test that article counts are computed correctly by company."""

    df = sample_mentions_dataframe()
    company_df = filter_company_article_rows(df)
    result_df = articles_by_company_count(company_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    # Apple mention_count = 3 + 2 + 2 = 7
    assert apple_row["article_count"] == 5

    # Tesla mention_count = 1 + 4 = 5
    assert tesla_row["article_count"] == 5


def test_add_share_of_voice():
    """Test that share of voice is calculated correctly and added to the dataframe."""

    article_counts_df = pd.DataFrame([
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_count": 5
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_count": 5
        }
    ])

    result_df = add_share_of_voice(article_counts_df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["share_of_voice"] == 5 / 10
    assert tesla_row["share_of_voice"] == 5 / 10


def test_share_of_voice_calculate():
    """Test that share of voice is calculated correctly
      from the original mentions dataframe."""

    df = sample_mentions_dataframe()
    result_df = share_of_voice_calculate(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    assert apple_row["article_count"] == 5
    assert tesla_row["article_count"] == 5
    assert apple_row["share_of_voice"] == 5 / 12
    assert tesla_row["share_of_voice"] == 5 / 12


def test_share_of_voice_empty_dataframe():
    """Test that calculating share of voice on 
    an empty dataframe returns an empty dataframe."""

    empty_df = pd.DataFrame(
        columns=[
            "entity_name", "entity_type",
            "article_guid", "mention_count"
        ]
    )

    result_df = share_of_voice_calculate(empty_df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type",
        "article_count", "share_of_voice"
    ]


def test_top_3_rows():
    """Test that top 3 rows are returned correctly based on the specified column."""

    df = pd.DataFrame([
        {"company": "A", "score": 1},
        {"company": "B", "score": 5},
        {"company": "C", "score": 3},
        {"company": "D", "score": 4}
    ])

    result_df = top_3_rows(df, "score")

    assert len(result_df) == 3
    assert list(result_df["company"]) == ["B", "D", "C"]


def test_bottom_3_rows():
    """Test that bottom 3 rows are returned 
    correctly based on the specified column."""

    df = pd.DataFrame([
        {"company": "A", "score": 0},
        {"company": "B", "score": 5},
        {"company": "C", "score": 3},
        {"company": "D", "score": 1},
        {"company": "E", "score": 2}
    ])

    result_df = bottom_3_rows(df, "score")

    assert len(result_df) == 3
    assert list(result_df["company"]) == ["D", "E", "C"]
