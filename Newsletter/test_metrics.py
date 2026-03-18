import pandas as pd

from metrics import (
    create_mentions_dataframe,
    compute_mention_volume,
    get_top_3_companies,
    get_bottom_3_companies,
)


def test_create_mentions_dataframe_returns_dataframe():
    items = [
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a2",
        },
    ]

    df = create_mentions_dataframe(items)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert "entity_id" in df.columns
    assert "article_id" in df.columns


def test_compute_mention_volume_counts_distinct_articles_only():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a2",
        },
    ])

    result = compute_mention_volume(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["mention_volume"] == 2


def test_compute_mention_volume_ignores_non_company_entities():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "p1",
            "entity_name": "Sam Altman",
            "entity_type": "person",
            "article_id": "a1",
        },
    ])

    result = compute_mention_volume(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["entity_type"] == "company"
    assert result.iloc[0]["mention_volume"] == 1


def test_compute_mention_volume_drops_rows_with_missing_required_values():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": None,
        },
        {
            "entity_id": None,
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a2",
        },
    ])

    result = compute_mention_volume(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["mention_volume"] == 1


def test_compute_mention_volume_sorts_highest_first():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1",
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a2",
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a3",
        },
    ])

    result = compute_mention_volume(df)

    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["mention_volume"] == 2
    assert result.iloc[1]["entity_id"] == "c2"
    assert result.iloc[1]["mention_volume"] == 1


def test_compute_mention_volume_returns_empty_dataframe_for_empty_input():
    df = pd.DataFrame()

    result = compute_mention_volume(df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    assert list(result.columns) == [
        "entity_id",
        "entity_name",
        "entity_type",
        "mention_volume",
    ]


def test_get_top_3_companies_returns_first_three_rows():
    mention_volume_df = pd.DataFrame([
        {"entity_id": "c1", "entity_name": "A",
            "entity_type": "company", "mention_volume": 10},
        {"entity_id": "c2", "entity_name": "B",
            "entity_type": "company", "mention_volume": 8},
        {"entity_id": "c3", "entity_name": "C",
            "entity_type": "company", "mention_volume": 6},
        {"entity_id": "c4", "entity_name": "D",
            "entity_type": "company", "mention_volume": 4},
    ])

    result = get_top_3_companies(mention_volume_df)

    assert len(result) == 3
    assert list(result["entity_id"]) == ["c1", "c2", "c3"]


def test_get_bottom_3_companies_returns_lowest_non_zero_rows():
    mention_volume_df = pd.DataFrame([
        {"entity_id": "c1", "entity_name": "A",
            "entity_type": "company", "mention_volume": 10},
        {"entity_id": "c2", "entity_name": "B",
            "entity_type": "company", "mention_volume": 2},
        {"entity_id": "c3", "entity_name": "C",
            "entity_type": "company", "mention_volume": 1},
        {"entity_id": "c4", "entity_name": "D",
            "entity_type": "company", "mention_volume": 0},
        {"entity_id": "c5", "entity_name": "E",
            "entity_type": "company", "mention_volume": 3},
    ])

    result = get_bottom_3_companies(mention_volume_df)

    assert len(result) == 3
    assert list(result["entity_id"]) == ["c3", "c2", "c5"]
    assert all(result["mention_volume"] > 0)


def test_get_bottom_3_companies_returns_fewer_if_less_than_three_non_zero():
    mention_volume_df = pd.DataFrame([
        {"entity_id": "c1", "entity_name": "A",
            "entity_type": "company", "mention_volume": 0},
        {"entity_id": "c2", "entity_name": "B",
            "entity_type": "company", "mention_volume": 2},
        {"entity_id": "c3", "entity_name": "C",
            "entity_type": "company", "mention_volume": 1},
    ])

    result = get_bottom_3_companies(mention_volume_df)

    assert len(result) == 2
    assert list(result["entity_id"]) == ["c3", "c2"]
