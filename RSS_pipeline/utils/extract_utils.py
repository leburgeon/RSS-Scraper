""" Functionality for polling RSS feed and extracting articles."""
from datetime import datetime

import feedparser
import requests
import logging
from bs4 import BeautifulSoup

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
        
    @staticmethod
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

    @staticmethod
    def _generate_pk_for_article(article_guid) -> str:
        """Generate a unique primary key for the article using its GUID."""
        return f"ARTICLE#{article_guid}"


def poll_rss_feed_for_articles(feed_url) -> list[Article]:
    """
    Polls RSS data using feedparser and returns a list of articles.
    """
    # feedparser.parse can take a URL, a file path, or a raw XML string
    feed = feedparser.parse(feed_url)

    articles = []

    for entry in feed.entries:
        
        articles.append(Article(
            article_guid=entry.get('id'),
            title=entry.get('title'),
            published_at=datetime.strptime(entry.get('published'), '%a, %d %b %Y %H:%M:%S %Z')
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









