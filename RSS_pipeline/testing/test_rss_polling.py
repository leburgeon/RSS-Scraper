import pytest

from RSS_pipeline.polling_utils import filter_articles_by_date

def test_filter_articles_by_date():
    """Tests filtering articles by publish date."""
    articles = [
        {"title": "Article 1", "publish_date": "Mon, 16 Mar 2026 07:14:05 GMT"},
        {"title": "Article 2", "publish_date": "Tue, 17 Mar 2026 08:00:00 GMT"},
        {"title": "Article 3", "publish_date": "Sun, 15 Mar 2026 06:00:00 GMT"},
        {"title": "Article 4", "publish_date": None},  # Missing publish date
        {"title": "Article 5", "publish_date": "Invalid Date Format"},  # Invalid date format
    ]

    most_recent_date = "Mon, 16 Mar 2026 07:14:05 GMT"
    filtered_articles = filter_articles_by_date(articles, most_recent_date)

    assert len(filtered_articles) == 1
    assert filtered_articles[0]['title'] == "Article 2"
