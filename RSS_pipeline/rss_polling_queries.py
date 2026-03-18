import boto3
import hashlib


def update_feed_metadata(feed_id: str, most_recent_article_datetime: str, table: boto3.resources.factory.dynamodb.Table):
    """
    Update feed metadata with new etag, last_modified and most recent article datetime.
    """
    response = table.update_item(
        Key={
            "PK": f"FEED#{feed_id}",
            "SK": "META"
        },
        UpdateExpression="SET most_recent_article_datetime = :most_recent_article_datetime",
        ExpressionAttributeValues={
            ":most_recent_article_datetime": most_recent_article_datetime
        },
        ReturnValues="UPDATED_NEW"
    )
    return response


def get_most_recent_article_datetime(feed_id: str, table: boto3.resources.factory.dynamodb.Table) -> str:
    """
    Get the most recent article datetime for a feed.
    """
    response = table.get_item(
        Key={
            "PK": f"FEED#{feed_id}",
            "SK": "META"
        }
    )
    item = response.get("Item", {})
    return item.get("most_recent_article_datetime", None)
