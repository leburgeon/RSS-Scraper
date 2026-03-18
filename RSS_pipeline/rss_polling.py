""" Functionality for polling RSS feed and extracting articles."""
from datetime import datetime

import feedparser
import requests
import logging
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

def poll_rss_feed_for_articles(feed_url) -> list:
    """
    Polls RSS data using feedparser and returns a list of articles.
    """
    # feedparser.parse can take a URL, a file path, or a raw XML string
    feed = feedparser.parse(feed_url)
    
    articles = []

    for entry in feed.entries:
        articles.append({
            "title": entry.get('title'),
            "link": entry.get('link'),
            "publish_date": entry.get('published'),
            "guid": entry.get('id'),
            "summary": entry.get('summary')         
        })

    return articles

def filter_articles_by_date(articles: list[dict], most_recent_date: str) -> list[dict]:
    """Filter out articles that are before a certain date"""
    most_recent_date = datetime.strptime(most_recent_date, '%a, %d %b %Y %H:%M:%S %Z')

    filtered_articles = []

    for article in articles:
        publish_date_str = article.get('publish_date')
        if publish_date_str:
            try:
                publish_date = datetime.strptime(publish_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                if publish_date > most_recent_date:
                    filtered_articles.append(article)
            except ValueError as e:
                logging.error(f"Error parsing publish date '{publish_date_str}': {e}")

    return filtered_articles


def get_html_content_from_article_link(article_link) -> str:
    """Fetch the HTML content of the article from its link."""
    try:
        response = requests.get(article_link)
        response.raise_for_status()  # Check if the request was successful
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching article content from {article_link}: {e}")
        return None


def extract_article_content(html_content) -> str:
    """Extract the main content of the article from its HTML."""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # This is a very basic extraction method. You may want to use more sophisticated methods or libraries like newspaper3k.
        paragraphs = soup.find_all('p')
        article_text = '\n'.join([para.get_text() for para in paragraphs])
        return article_text
    except Exception as e:
        logging.error(f"Error extracting article content: {e}")
        return None
    
if __name__ == "__main__":
    feed_url = "https://www.theguardian.com/technology/rss"  # Replace with your RSS feed URL

    articles = poll_rss_feed_for_articles(feed_url)
    
    print(f"Found {len(articles)} articles in the RSS feed.")

    filtered_articles = filter_articles_by_date(articles, "Mon, 16 Mar 2026 07:14:05 GMT")
    print(f"{len(filtered_articles)} articles published after the specified date.")
        