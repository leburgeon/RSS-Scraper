from datetime import datetime, timedelta

import boto3
import logging
from typing import Any


def logging_setup():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


logger = logging_setup()


def insert_item(item: dict, table: Any):
    """Insert a item into the database.
    """
    # add error handling for empty item
    if not item:
        logger.warning("No item to insert.")
        return

    try:
        response = table.put_item(Item=item)
        return response
    except Exception as e:
        logger.error(f"Error inserting item: {e}")
        raise


def insert_items(items: list[dict], table: Any):
    """Insert multiple items into the database.
    """
    # add error handling for empty list
    if not items:
        logger.warning("No items to insert.")
        return

    try:
        for item in items:
            insert_item(item, table)
    except Exception as e:
        logger.error(f"Error inserting items: {e}")
        raise


def insert_feed_metadata(feed_metadata: dict, table: Any):
    # Code to insert feed metadata into the database

    try:
        table.put_item(Item=feed_metadata)
        logger.info(f"Inserted feed metadata for feed: {feed_metadata['PK']}")
    except Exception as e:
        logger.error(f"Error inserting feed metadata: {e}")


def update_feed_latest_article_date(feed_pk: str, new_date: str, table: Any):
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


def get_latest_article_date(feed_pk: str, table: Any) -> str | None:
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
        "FEED#techcrunch", str((datetime.now() - timedelta(days=1)).isoformat()), table)

    # Retrieve the latest article date
    latest_date = get_latest_article_date(
        "FEED#techcrunch", table)
    logger.info(
        f"Latest article date for FEED#techcrunch: {latest_date}")
    print(type(latest_date))
