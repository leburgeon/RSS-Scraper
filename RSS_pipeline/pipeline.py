import os

from utils.extract_utils import poll_rss_feed_for_articles, filter_articles_by_date, get_most_recent_article_datetime
from utils.extract_utils import Article
from utils.transform_utils import (
    extract_entities,
    extract_sentiments_and_counts_per_entity,
    setup_nlp
)
from dotenv import load_dotenv
import boto3

load_dotenv()

FEED_URL = os.getenv("FEED_URL")
TABLE_NAME = os.getenv("TABLE_NAME")



def main():

    # Get the most recent article date from the database to filter new articles
    table = boto3.resource('dynamodb').Table(TABLE_NAME)
    most_recent_article_date = get_most_recent_article_datetime("FEED#guardian-tech", table)
    print(f"Most recent article date from DB: {most_recent_article_date}")

    # # Extract all the rss articles
    # articles = poll_rss_feed_for_articles(FEED_URL)
    # print(f"Extracted {len(articles)} articles from the RSS feed.")
    
    # # TODO filter articles by date using the most recent article date from the database
    # filtered_articles = articles[:1]

    # # Transform the articles (e.g. extract article content, generate PKs, etc.)
    # entity_mentions = []

    # nlp = setup_nlp()

    # for article in filtered_articles:
    #     entities = extract_entities(article.article_content, nlp)
    #     sentiments_and_counts = extract_sentiments_and_counts_per_entity(article.article_content, entities)
    #     entity_mentions.extend(sentiments_and_counts)

    # print(f"Extracted entity mentions and sentiments for {len(entity_mentions)} entities.")
    # print(entity_mentions)

    # # Load entity mentions and sentiments into the database

    

if __name__ == "__main__":
    main()