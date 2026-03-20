"""Utility functions for cleaning the database."""
from typing import Any
import logging
import boto3

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_articles_and_mentions(
        table: Any) -> bool:
    """
    Delete all articles and mentions.

    Scans entire table and removes
    items starting with ARTICLE# or
    MENTION_DATE#. Returns True on
    success.
    """
    try:
        response = table.scan()
        items = response.get("Items", [])

        batch_size = 200
        for i in range(0, len(items),
                       batch_size):
            batch = items[i:i + batch_size]
            delete_batch(batch, table)

        return True
    except Exception as e:
        logger.error(
            f"Error clearing database: {e}")
        return False


def delete_batch(items: list, table):
    """Delete a batch of items."""
    with table.batch_writer() as batch:
        for item in items:
            pk = item.get("PK", "")
            if (pk.startswith("ARTICLE#") or
                    pk.startswith(
                        "MENTION_DATE#")):
                sk = item.get("SK", "")
                batch.delete_item(
                    Key={"PK": pk, "SK": sk})


if __name__ == "__main__":
    # Example usage
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("c22-rss-scraper-table")

    success = clear_articles_and_mentions(table)
    if success:
        logger.info("Database cleared successfully.")
    else:
        logger.error("Failed to clear database.")
