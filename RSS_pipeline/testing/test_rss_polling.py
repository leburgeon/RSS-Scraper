import pytest
from datetime import datetime
from ..utils.extract_utils import Article, filter_articles_by_date

ARTICLE_1_DATE = datetime(2026, 3, 16, 7, 14, 5)
ARTICLE_2_DATE = datetime(2026, 3, 17, 8, 0, 0)
ARTICLE_3_DATE = datetime(2026, 3, 15, 6, 0, 0)


@pytest.fixture
def test_articles():
    """Create test Article objects."""
    article_1 = Article(
        article_guid="guid1",
        title="Article 1",
        published_at=ARTICLE_1_DATE,
    )
    article_2 = Article(
        article_guid="guid2",
        title="Article 2",
        published_at=ARTICLE_2_DATE,
    )
    article_3 = Article(
        article_guid="guid3",
        title="Article 3",
        published_at=ARTICLE_3_DATE,
    )
    return [article_1, article_2, article_3]


def test_filter_articles_by_date(test_articles):
    """Filter articles published after a \
    date."""
    cutoff_date = (
        ARTICLE_1_DATE.isoformat()
    )
    filtered_articles = filter_articles_by_date(
        test_articles,
        cutoff_date,
    )
    assert len(filtered_articles) == 1
    assert filtered_articles[0].title == (
        "Article 2"
    )
