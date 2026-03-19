""" Functionality for polling RSS feed and extracting articles."""
from datetime import datetime

import feedparser
import requests
import logging
from bs4 import BeautifulSoup
import hashlib

logging.basicConfig(level=logging.INFO)


class Article:
    def __init__(self, pk: str, article_guid: str, title: str, published_at: datetime):
        self.pk = pk
        self.sk = "meta"
        self.article_guid = article_guid
        self.title = title
        self.published_at = published_at
        self.article_content = Article._extract_article_content(article_guid)

    def to_item_format(self) -> dict: 
        return {
            "pk": self.pk,
            "sk": self.sk,
            "article_guid": self.article_guid,
            "title": self.title,
            "article_content": self.article_content,
            "published_at": self.published_at.isoformat()
        }
    
    def _get_html_content_from_article_link(article_link) -> str:
        """Fetch the HTML content of the article from its link."""
        try:
            response = requests.get(article_link)
            response.raise_for_status()  # Check if the request was successful
            return response.text
        except requests.RequestException as e:
            logging.error(
                f"Error fetching article content from {article_link}: {e}")
            return None
        
    def _extract_article_content(article_link) -> str:
        """Extract the main content of an article from its article link."""
        try:
            html_content = Article._get_html_content_from_article_link(article_link)
            soup = BeautifulSoup(html_content, 'html.parser')
            # This is a very basic extraction method. You may want to use more sophisticated methods or libraries like newspaper3k.
            paragraphs = soup.find_all('p')
            article_text = '\n'.join([para.get_text() for para in paragraphs])
            return article_text
        except Exception as e:
            logging.error(f"Error extracting article content: {e}")
            return None


def poll_rss_feed_for_articles(feed_url) -> list[Article]:
    """
    Polls RSS data using feedparser and returns a list of articles.
    """
    # feedparser.parse can take a URL, a file path, or a raw XML string
    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:
        
        articles.append(Article(        
            pk=entry.get('id'),
            article_guid=entry.get('id'),
            title=entry.get('title'),
            published_at=datetime.strptime(entry.get('published'), '%a, %d %b %Y %H:%M:%S %Z')
        ))

    return articles


def filter_articles_by_date(articles: list[Article], most_recent_date: str) -> list[Article]:
    """Filter out articles that are before a certain date"""









