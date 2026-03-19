""" Functionality for polling RSS feed and extracting articles."""
from datetime import datetime
from email.utils import parsedate_to_datetime

import feedparser
import requests
import logging
from bs4 import BeautifulSoup
import boto3
from typing import Any

logging.basicConfig(level=logging.INFO)


class Article:
    """Class representing an article extracted from the RSS feed."""

    def __init__(self, article_guid: str, title: str, published_at: datetime):
        self.pk = Article._generate_pk_for_article(article_guid)
        self.sk = "META"
        self.article_guid = article_guid
        self.title = title
        self.published_at = published_at
        self.article_content = Article._extract_article_content(article_guid)

    def to_item_format(self) -> dict:
        """Convert the Article object to a dictionary format suitable for database insertion."""
        return {
            "PK": self.pk,
            "SK": self.sk,
            "article_guid": self.article_guid,
            "title": self.title,
            "published_at": self.published_at.isoformat(),
            "article_content": self.article_content

        }

    @staticmethod
    def _get_html_content_from_article_link(
            article_link) -> str:
        """Fetch HTML from article link."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; "
                "Win64; x64) AppleWebKit/537.36"
            )
        }
        try:
            response = requests.get(
                article_link,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(
                f"Error fetching {article_link}: "
                f"{e}")
            return None

    @staticmethod
    def _extract_article_content(article_link) -> str:
        """Extract the main content of an article from its article link."""
        try:
            html_content = Article._get_html_content_from_article_link(
                article_link)
            soup = BeautifulSoup(html_content, 'html.parser')

            paragraphs = soup.find_all('p')
            article_text = '\n'.join([para.get_text() for para in paragraphs])
            return article_text
        except Exception as e:
            logging.error(f"Error extracting article content: {e}")
            return None

    @staticmethod
    def _generate_pk_for_article(article_guid) -> str:
        """Generate a unique primary key for the article using its GUID."""
        return f"ARTICLE#{article_guid}"


def get_all_feed_urls_and_pks(table: Any) -> list[tuple[str, str]]:
    """Get all feed PKs and URLs from database.

    Returns list of (pk, feed_url) tuples.
    """
    response = table.scan(
        FilterExpression=(
            "item_type = :type AND SK = :sk"
        ),
        ExpressionAttributeValues={
            ":type": "FEED",
            ":sk": "META"
        }
    )

    feeds = [
        (item["PK"], item["feed_url"])
        for item in response.get("Items", [])
    ]
    return feeds


def poll_rss_feed_for_articles(feed_url) -> list[Article]:
    """
    Polls RSS data using feedparser and returns a list of articles.
    """
    # feedparser.parse can take a URL, a file path, or a raw XML string
    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:
        parsed_dt = parsedate_to_datetime(entry.get('published'))
        articles.append(Article(
            article_guid=entry.get('id'),
            title=entry.get('title'),
            published_at=parsed_dt.replace(tzinfo=None)
        ))

    return articles


def filter_articles_by_date(articles: list[Article], latest_article_date: str = None) -> list[Article]:
    """Filter articles published strictly after latest_article_date.
    Expects latest_article_date as an ISO 8601 string.
    Articles with unparseable dates are excluded.
    """
    if latest_article_date is None:
        return articles

    cutoff = datetime.fromisoformat(latest_article_date)
    filtered = []
    for article in articles:
        if article.published_at > cutoff:
            filtered.append(article)
    return filtered


if __name__ == "__main__":

    table = boto3.resource("dynamodb").Table("c22-rss-scraper-table")

    feed_data = get_all_feed_urls_and_pks(table)
    logging.info(f"Retrieved {len(feed_data)} feed URLs from the database.")
    print(feed_data)
