import pandas as pd

from metrics import (
    create_mentions_dataframe,
    compute_mention_volume,
    filter_company_sentiment_rows,
    get_top_3_rows,
    get_bottom_3_rows,
    count_sentiment_by_company,
    add_sentiment_percentages,
    compute_sentiment_distribution,
    filter_company_article_rows,
    count_articles_by_company,
    add_share_of_voice,
    compute_share_of_voice,
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


def test_get_top_3_rows_returns_first_three_rows():
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

    result = get_top_3_rows(mention_volume_df, "mention_volume")

    assert len(result) == 3
    assert list(result["entity_id"]) == ["c1", "c2", "c3"]


def test_get_bottom_3_rows_returns_lowest_non_zero_rows():
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

    result = get_bottom_3_rows(mention_volume_df, "mention_volume")

    assert len(result) == 3
    assert list(result["entity_id"]) == ["c3", "c2", "c5"]
    assert all(result["mention_volume"] > 0)


def test_get_bottom_3_rows_returns_fewer_if_less_than_three_non_zero():
    mention_volume_df = pd.DataFrame([
        {"entity_id": "c1", "entity_name": "A",
            "entity_type": "company", "mention_volume": 0},
        {"entity_id": "c2", "entity_name": "B",
            "entity_type": "company", "mention_volume": 2},
        {"entity_id": "c3", "entity_name": "C",
            "entity_type": "company", "mention_volume": 1},
    ])

    result = get_bottom_3_rows(mention_volume_df, "mention_volume")

    assert len(result) == 2
    assert list(result["entity_id"]) == ["c3", "c2"]


def test_filter_company_sentiment_rows_keeps_only_company_rows():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "p1",
            "entity_name": "Sam Altman",
            "entity_type": "person",
            "sentiment": "neutral"
        }
    ])

    result = filter_company_sentiment_rows(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["entity_type"] == "company"


def test_filter_company_sentiment_rows_drops_missing_values():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "sentiment": None
        }
    ])

    result = filter_company_sentiment_rows(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"


def test_count_sentiment_by_company_counts_each_sentiment_correctly():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "neutral"
        }
    ])

    result = count_sentiment_by_company(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["positive"] == 2
    assert result.iloc[0]["neutral"] == 1
    assert result.iloc[0]["negative"] == 0


def test_count_sentiment_by_company_adds_missing_sentiment_columns():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        }
    ])

    result = count_sentiment_by_company(df)

    assert "positive" in result.columns
    assert "neutral" in result.columns
    assert "negative" in result.columns
    assert result.iloc[0]["positive"] == 1
    assert result.iloc[0]["neutral"] == 0
    assert result.iloc[0]["negative"] == 0


def test_add_sentiment_percentages_calculates_percentages_correctly():
    sentiment_counts_df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "positive": 2,
            "neutral": 1,
            "negative": 1
        }
    ])

    result = add_sentiment_percentages(sentiment_counts_df)

    assert result.iloc[0]["total"] == 4
    assert result.iloc[0]["positive_pct"] == 0.5
    assert result.iloc[0]["neutral_pct"] == 0.25
    assert result.iloc[0]["negative_pct"] == 0.25


def test_compute_sentiment_distribution_returns_expected_columns():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "neutral"
        }
    ])

    result = compute_sentiment_distribution(df)

    expected_columns = [
        "entity_id",
        "entity_name",
        "entity_type",
        "negative",
        "neutral",
        "positive",
        "total",
        "positive_pct",
        "neutral_pct",
        "negative_pct"
    ]

    for column in expected_columns:
        assert column in result.columns


def test_compute_sentiment_distribution_sorts_by_positive_pct_descending():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "sentiment": "neutral"
        }
    ])

    result = compute_sentiment_distribution(df)

    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["positive_pct"] == 1.0
    assert result.iloc[1]["entity_id"] == "c2"
    assert result.iloc[1]["positive_pct"] == 0.0


def test_compute_sentiment_distribution_handles_multiple_companies():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "positive"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "sentiment": "negative"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "sentiment": "neutral"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "sentiment": "neutral"
        }
    ])

    result = compute_sentiment_distribution(df)

    assert len(result) == 2

    openai_row = result[result["entity_id"] == "c1"].iloc[0]
    google_row = result[result["entity_id"] == "c2"].iloc[0]

    assert openai_row["positive"] == 1
    assert openai_row["negative"] == 1
    assert openai_row["neutral"] == 0
    assert openai_row["total"] == 2

    assert google_row["positive"] == 0
    assert google_row["negative"] == 0
    assert google_row["neutral"] == 2
    assert google_row["total"] == 2


def test_filter_company_article_rows_keeps_only_company_rows():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "p1",
            "entity_name": "Sam Altman",
            "entity_type": "person",
            "article_id": "a1"
        }
    ])

    result = filter_company_article_rows(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["entity_type"] == "company"


def test_filter_company_article_rows_drops_missing_values():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": None
        }
    ])

    result = filter_company_article_rows(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"


def test_count_articles_by_company_counts_distinct_articles_only():
    company_df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a2"
        }
    ])

    result = count_articles_by_company(company_df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["article_count"] == 2


def test_count_articles_by_company_handles_multiple_companies():
    company_df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a2"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a3"
        }
    ])

    result = count_articles_by_company(company_df)

    assert len(result) == 2

    openai_row = result[result["entity_id"] == "c1"].iloc[0]
    google_row = result[result["entity_id"] == "c2"].iloc[0]

    assert openai_row["article_count"] == 2
    assert google_row["article_count"] == 1


def test_add_share_of_voice_calculates_correct_proportions():
    article_counts_df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_count": 2
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_count": 1
        }
    ])

    result = add_share_of_voice(article_counts_df)

    openai_row = result[result["entity_id"] == "c1"].iloc[0]
    google_row = result[result["entity_id"] == "c2"].iloc[0]

    assert openai_row["share_of_voice"] == 2 / 3
    assert google_row["share_of_voice"] == 1 / 3


def test_add_share_of_voice_returns_zero_when_total_article_mentions_is_zero():
    article_counts_df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_count": 0
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_count": 0
        }
    ])

    result = add_share_of_voice(article_counts_df)

    assert all(result["share_of_voice"] == 0)


def test_compute_share_of_voice_returns_expected_columns():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a2"
        }
    ])

    result = compute_share_of_voice(df)

    expected_columns = [
        "entity_id",
        "entity_name",
        "entity_type",
        "article_count",
        "share_of_voice"
    ]

    assert list(result.columns) == expected_columns


def test_compute_share_of_voice_sorts_highest_first():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a2"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a3"
        }
    ])

    result = compute_share_of_voice(df)

    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[1]["entity_id"] == "c2"
    assert result.iloc[0]["share_of_voice"] > result.iloc[1]["share_of_voice"]


def test_compute_share_of_voice_ignores_non_company_rows():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "p1",
            "entity_name": "Sam Altman",
            "entity_type": "person",
            "article_id": "a2"
        }
    ])

    result = compute_share_of_voice(df)

    assert len(result) == 1
    assert result.iloc[0]["entity_id"] == "c1"
    assert result.iloc[0]["article_count"] == 1


def test_compute_share_of_voice_counts_duplicate_company_article_once():
    df = pd.DataFrame([
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c1",
            "entity_name": "OpenAI",
            "entity_type": "company",
            "article_id": "a1"
        },
        {
            "entity_id": "c2",
            "entity_name": "Google",
            "entity_type": "company",
            "article_id": "a2"
        }
    ])

    result = compute_share_of_voice(df)

    openai_row = result[result["entity_id"] == "c1"].iloc[0]
    google_row = result[result["entity_id"] == "c2"].iloc[0]

    assert openai_row["article_count"] == 1
    assert google_row["article_count"] == 1
    assert openai_row["share_of_voice"] == 0.5
    assert google_row["share_of_voice"] == 0.5
