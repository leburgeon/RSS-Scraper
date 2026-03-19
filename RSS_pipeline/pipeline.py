import os

from utils.extract_utils import poll_rss_feed_for_articles, filter_articles_by_date
from utils.extract_utils import Article
from utils.transform_utils import (
    extract_entities,
    extract_sentiments_and_counts_per_entity,
)
from dotenv import load_dotenv

load_dotenv()

FEED_URL = os.getenv("FEED_URL")



def main():

    # Get most recent article date from the database
    
    # Extract all the rss articles
    articles = poll_rss_feed_for_articles(FEED_URL)
    print(f"Extracted {len(articles)} articles from the RSS feed.")
    
    # TODO filter articles by date using the most recent article date from the database
    filtered_articles = articles

    # Transform the articles (e.g. extract article content, generate PKs, etc.)
    entity_mentions = []

    for article in filtered_articles:
        entities = extract_entities(article.article_content)
        sentiments_and_counts = extract_sentiments_and_counts_per_entity(article.article_content, entities)
        entity_mentions.extend(sentiments_and_counts)

    print(f"Extracted entity mentions and sentiments for {len(entity_mentions)} entities.")






if __name__ == "__main__":
    main()