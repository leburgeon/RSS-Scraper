""" Functionality for polling RSS feed and extracting articles."""
import feedparser
import requests
import logging

logging.basicConfig(level=logging.INFO)

def poll_rss_feed_for_articles(feed_url) -> list:
    """Poll the RSS feed and return a list of articles."""
    feed = feedparser.parse(feed_url)
    articles = []
    for entry in feed.entries:
        article = {
            'title': entry.title,
            'link': entry.link,
            'published': entry.published,
            'summary': entry.summary,
            'guid': entry.guid if 'guid' in entry else entry.link  # Use link as guid if guid is not available
        }
        articles.append(article)
    return articles

def filter_articles_by_guid(articles, seen_guids) -> list:
    """Filter out articles that have already been seen based on their GUID."""
    new_articles = []
    for article in articles:
        if article['guid'] not in seen_guids:
            new_articles.append(article)
            seen_guids.add(article['guid'])  # Add the GUID to the set of seen GUIDs
    return new_articles

def get_html_content_from_article_link(article_link) -> str:
    """Fetch the HTML content of the article from its link."""
    try:
        response = requests.get(article_link)
        response.raise_for_status()  # Check if the request was successful
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching article content from {article_link}: {e}")
        return None


