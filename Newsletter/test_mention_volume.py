import pandas as pd

from metrics import (
    mentions_dataframe_creation,
    filter_company_rows,
    compute_mention_volume,
    top_3_rows,
    bottom_3_rows,
)


def sample_mentions_df():
    """Create a simple dataframe for mention volume tests."""
    data = [
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a1",
            "mention_count": 2,
            "sentiment": "positive",
        },
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a2",
            "mention_count": 1,
            "sentiment": "neutral",
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a1",
            "mention_count": 3,
            "sentiment": "negative",
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a3",
            "mention_count": 1,
            "sentiment": "positive",
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a4",
            "mention_count": 2,
            "sentiment": "neutral",
        },
        {
            "entity_name": "Meta",
            "entity_type": "company",
            "article_guid": "a5",
            "mention_count": 1,
            "sentiment": "positive",
        },
        {
            "entity_name": "Guardian",
            "entity_type": "company",
            "article_guid": "a6",
            "mention_count": 5,
            "sentiment": "positive",
        },
        {
            "entity_name": "Elon Musk",
            "entity_type": "person",
            "article_guid": "a7",
            "mention_count": 1,
            "sentiment": "positive",
        },
    ]
    return pd.DataFrame(data)


def test_mentions_dataframe_creation_returns_dataframe():
    """Test that mentions_dataframe_creation returns a dataframe with the expected columns."""
    items = [
        {"entity_name": "Apple", "entity_type": "company", "article_guid": "a1"}
    ]

    df = mentions_dataframe_creation(items)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1


def test_filter_company_rows_keeps_only_valid_companies():
    """Test that filtering for company rows only keeps valid
      company rows and excludes non-company and excluded entities."""

    df = sample_mentions_df()

    filtered_df = filter_company_rows(
        df,
        ["entity_name", "entity_type", "article_guid"],
        "Testing mention volume filter"
    )

    assert all(filtered_df["entity_type"] == "company")
    assert "Guardian" not in filtered_df["entity_name"].tolist()
    assert "Elon Musk" not in filtered_df["entity_name"].tolist()


def test_compute_mention_volume_counts_rows_per_company():
    """Test that mention volume is computed as the count of rows per company."""

    df = sample_mentions_df()

    result_df = compute_mention_volume(df)

    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]
    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    meta_row = result_df[result_df["entity_name"] == "Meta"].iloc[0]

    assert tesla_row["mention_volume"] == 3
    assert apple_row["mention_volume"] == 2
    assert meta_row["mention_volume"] == 1


def test_compute_mention_volume_excludes_guardian_and_non_company_rows():
    """Test that mention volume computation excludes 
    rows for Guardian and non-company entities."""

    df = sample_mentions_df()

    result_df = compute_mention_volume(df)

    names = result_df["entity_name"].tolist()

    assert "Guardian" not in names
    assert "Elon Musk" not in names


def test_compute_mention_volume_returns_empty_dataframe_for_empty_input():
    """Test that mention volume computation returns an empty dataframe 
    with the expected columns when given an empty dataframe."""

    df = pd.DataFrame(columns=["entity_name", "entity_type", "article_guid"])

    result_df = compute_mention_volume(df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type", "mention_volume"]


def test_top_3_rows_returns_highest_mention_volume_rows():
    """Test that top_3_rows returns the 3 rows with the highest mention volume"""

    df = sample_mentions_df()
    mention_volume_df = compute_mention_volume(df)

    result_df = top_3_rows(mention_volume_df, "mention_volume")

    assert len(result_df) == 3
    assert result_df.iloc[0]["entity_name"] == "Tesla"


def test_bottom_3_rows_returns_lowest_non_zero_mention_volume_rows():
    """Test that bottom_3_rows returns the 3 rows with the lowest non-zero mention volume"""

    df = sample_mentions_df()
    mention_volume_df = compute_mention_volume(df)

    result_df = bottom_3_rows(mention_volume_df, "mention_volume")

    assert len(result_df) == 3
    assert all(result_df["mention_volume"] > 0)
    assert result_df.iloc[0]["mention_volume"] <= result_df.iloc[-1]["mention_volume"]
