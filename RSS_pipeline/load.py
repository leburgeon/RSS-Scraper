"""
This script contains functions for loading and preprocessing data for the RSS pipeline.
This includes functions error handling and loading data to awsDynamoDB. """

import boto3
import logging


def logging_setup():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)


logger = logging_setup()


def insert_item(item: dict, table: boto3.resources.factory.dynamodb.Table):
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


def insert_items(items: list[dict], table: boto3.resources.factory.dynamodb.Table):
    """Insert multiple items into the database.
    """
    # add error handling for empty list
    if not items:
        logger.warning("No items to insert.")
        return

    try:
        with table.batch_writer() as batch:
            for item in items:
                batch.put_item(Item=item)
    except Exception as e:
        logger.error(f"Error inserting items: {e}")
        raise
