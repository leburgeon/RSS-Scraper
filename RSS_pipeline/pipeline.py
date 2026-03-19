import logging
import os

from utils.extract_utils import poll_rss_feed_for_articles, filter_articles_by_date
from utils.transform_utils import (
    EntityMention,
    extract_entities,
    extract_sentiments_and_counts_per_entity,
    setup_nlp
)
from utils.load_utils import get_latest_article_date, update_feed_latest_article_date, insert_items
from dotenv import load_dotenv
import boto3

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FEED_URL = os.getenv("FEED_URL")
TABLE_NAME = os.getenv("TABLE_NAME")

def insert_articles(articles, table):
    # Code to insert articles into the database
    transformed_articles = [article.to_item_format() for article in articles]
    insert_items(transformed_articles, table)

def extract_articles(table):
    """ Extract articles from the RSS feed, filter by date, and return the articles to be loaded into the database."""
    most_recent_article_date: str = get_latest_article_date("FEED#guardian-tech", table)
    logging.info(f"Most recent article date from DB: {most_recent_article_date}")

    # Extract all the rss articles
    articles = poll_rss_feed_for_articles(FEED_URL)
    logging.info(f"Extracted {len(articles)} articles from the RSS feed.")

    # Filter articles by date using the most recent article date from the database
    filtered_articles = filter_articles_by_date(articles, most_recent_article_date)
    logging.info(f"{len(filtered_articles)} articles published after {most_recent_article_date}.")

    return filtered_articles

def load_articles(filtered_articles, table):
    """ Load the articles into the database and update the most recent article date for the feed."""
    # Insert new articles into the database
    insert_articles(filtered_articles, table)

    # Load articles into the database and update the most recent article date for the feed
    if filtered_articles:
        latest_date_in_batch = max(article.published_at for article in filtered_articles).isoformat()
        update_feed_latest_article_date("FEED#guardian-tech", latest_date_in_batch, table)
        logging.info(f"Updated latest article date in DB to: {latest_date_in_batch}")
    else:
        logging.info("No new articles to process. Exiting.")
        return



def extract_entity_mentions_and_sentiments(articles) -> list[EntityMention]:
    """ Transform the article content to extract entities and sentiments, and return these in a format suitable for database insertion."""
    entity_mentions = []

    # Set up the NLP pipeline once and reuse it for all articles to improve performance
    nlp = setup_nlp()

    # Loop through each article and extract entities and sentiments
    for article in articles:
        # Extract entities for article
        entities = extract_entities(article.article_content, nlp)

        # Extract sentiments and counts for each entity in the article
        sentiments_and_counts = extract_sentiments_and_counts_per_entity(article.article_content, entities)

        # Enrich the extracted entity mentions with article metadata for downstream processing and analysis, and convert to item format for database insertion
        enriched_entity_mentions = EntityMention.enrich_entity_mentions_with_article_metadata(sentiments_and_counts, article)
        
        entity_mentions.extend(enriched_entity_mentions)

    logging.info(f"Extracted entity mentions and sentiments for {len(entity_mentions)} entities.")

    return entity_mentions

def load_entity_mentions(entity_mentions, table):
    """ Load the extracted entity mentions into the database."""
    # Convert entity mentions to item format for database insertion
    items_to_insert = [entity.to_item_format() for entity in entity_mentions]

    # Insert entity mentions into the database
    insert_items(items_to_insert, table)



def main():

    # DELETE THIS
    update_feed_latest_article_date("FEED#guardian-tech", "2026-03-19T00:00:00", boto3.resource('dynamodb').Table(TABLE_NAME))

    # Get the most recent article date from the database to filter new articles
    table = boto3.resource('dynamodb').Table(TABLE_NAME)

    # Extract the articles from the RSS feed and filter by date
    articles_to_load = extract_articles(table)[:1]

    # Load the articles into the database and update the most recent article date for the feed
    load_articles(articles_to_load, table)

    # Extract entities and sentiments for the articles to be loaded, enrich with article metadata, and convert to item format for database insertion
    enriched_entity_mentions = extract_entity_mentions_and_sentiments(articles_to_load)

    # Load the extracted entity mentions into the database
    load_entity_mentions(enriched_entity_mentions, table)


    

if __name__ == "__main__":
    main()