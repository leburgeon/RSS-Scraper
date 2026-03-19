import os

from utils.extract_utils import poll_rss_feed_for_articles, filter_articles_by_date
from utils.extract_utils import Article
from utils.transform_utils import (
    extract_entities,
    extract_sentiments_and_counts_per_entity,
    setup_nlp
)
from utils.load_utils import get_latest_article_date, update_feed_latest_article_date, insert_items
from dotenv import load_dotenv
import boto3

load_dotenv()

FEED_URL = os.getenv("FEED_URL")
TABLE_NAME = os.getenv("TABLE_NAME")



def main():

    # Get the most recent article date from the database to filter new articles
    table = boto3.resource('dynamodb').Table(TABLE_NAME)
    most_recent_article_date: str = get_latest_article_date("FEED#guardian-tech", table)

    print(f"Most recent article date from DB: {most_recent_article_date}")

    # Extract all the rss articles
    articles = poll_rss_feed_for_articles(FEED_URL)
    print(f"Extracted {len(articles)} articles from the RSS feed.")

    # Filter articles by date using the most recent article date from the database
    filtered_articles = filter_articles_by_date(articles, most_recent_article_date)
    print(f"{len(filtered_articles)} articles published after {most_recent_article_date}.")

    # Load articles into the database and update the most recent article date for the feed
    if filtered_articles:
        latest_date_in_batch = max(article.published_at for article in filtered_articles).isoformat()
        update_feed_latest_article_date("FEED#guardian-tech", latest_date_in_batch, table)
        print(f"Updated latest article date in DB to: {latest_date_in_batch}")
    else:
        print("No new articles to process. Exiting.")
        return
    
    # Insert articles into the database 
    transformed_articles = [article.to_item_format() for article in filtered_articles]
    insert_items(transformed_articles, table)

    # Query table to check if articles have been added
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key('pk').begins_with("ARTICLE#")
    )
    print(f"Number of articles in DB after insertion: {len(response['Items'])}")
    print("Sample article item from DB:", response['Items'][0] if response['Items'] else "No articles found in DB.")

    # # Transform the article content to extract entities and sentiments, and load these into the database as well
    # entity_mentions = []

    # nlp = setup_nlp()

    # for article in filtered_articles:
    #     entities = extract_entities(article.article_content, nlp)
    #     sentiments_and_counts = extract_sentiments_and_counts_per_entity(article.article_content, entities)
    #     entity_mentions.extend(sentiments_and_counts)

    # print(f"Extracted entity mentions and sentiments for {len(entity_mentions)} entities.")
    # print(entity_mentions)

    

if __name__ == "__main__":
    main()