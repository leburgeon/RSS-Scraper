from typing import Any
import logging
import boto3
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_feed_metadata(feed_metadata, table: Any):
    # Code to insert feed metadata into the database

    try:
        table.put_item(Item=feed_metadata)
        logger.info(f"Inserted feed metadata for feed: {feed_metadata['PK']}")
    except Exception as e:
        logger.error(f"Error inserting feed metadata: {e}")


def update_feed_latest_article_date(feed_pk, new_date, table: Any):
    # Code to update existing feed metadata in the database
    try:
        table.update_item(
            Key={"PK": feed_pk, "SK": "META"},
            UpdateExpression="SET latest_article_date = :new_date",
            ExpressionAttributeValues={":new_date": new_date},
        )
        logger.info(
            f"Updated latest article date for feed: {feed_pk} to {new_date}")
    except Exception as e:
        logger.error(f"Error updating feed metadata: {e}")


def get_latest_article_date(feed_pk, table: Any):
    # Code to retrieve the latest article date for a given feed
    try:
        response = table.get_item(Key={"PK": feed_pk, "SK": "META"})
        item = response.get("Item")
        if item:
            return item.get("latest_article_date")
    except Exception as e:
        logger.error(f"Error retrieving latest article date: {e}")
    return None


if __name__ == "__main__":
    # Example usage
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("c22-rss-scraper-table")

    feed_metadata_techcrunch = {
        "PK": "FEED#techcrunch",
        "SK": "META",
        "item_type": "FEED",
        "feed_url": "https://techcrunch.com/feed/",
        "latest_article_date": ""
    }

    insert_feed_metadata(feed_metadata_techcrunch, table)

    # Update the latest article date
    update_feed_latest_article_date(
        "FEED#techcrunch", (datetime.now() - timedelta(days=1)).isoformat(), table)

    # Retrieve the latest article date
    latest_date = get_latest_article_date(
        "FEED#techcrunch", table)
    logger.info(
        f"Latest article date for FEED#techcrunch: {latest_date}")
    print(type(latest_date))
