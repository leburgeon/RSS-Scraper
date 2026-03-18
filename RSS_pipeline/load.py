"""
This script contains functions for loading and preprocessing data for the RSS pipeline.
This includes functions error handling and loading data to awsDynamoDB. """

import boto3


def insert_item(item: dict, table: boto3.resources.factory.dynamodb.Table):
    """Insert a item into the database.
    """
    response = table.put_item(Item=item)
    return response


def insert_items(items: list[dict], table: boto3.resources.factory.dynamodb.Table):
    """Insert multiple items into the database.
    """
    with table.batch_writer() as batch:
        for item in items:
            batch.put_item(Item=item)
