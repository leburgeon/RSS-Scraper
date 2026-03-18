import boto3
import hashlib

dynamodb = boto3.resource(
    "dynamodb",
    region_name="eu-west-2"
)

table = dynamodb.Table(
    "c22_charlie_media_mvp"
)

# update feed metadata with new etag and last_modified and most recent published article datetime


def update_feed_metadata(feed_id: str, etag: str, last_modified: str, most_recent_article_datetime: str):
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


def get_most_recent_article_datetime(feed_id: str) -> str:
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


def generate_article_id(feed_id: str, guid: str) -> str:
    """
    Generate a unique article ID based on feed ID and article GUID.
    """
    unique_id = hashlib.sha256(guid.encode('utf-8')).hexdigest()

    return f"{feed_id}#{unique_id}"
