import boto3
from datetime import datetime

dynamodb = boto3.resource(
    "dynamodb",
    region_name="eu-west-2"
)

table = dynamodb.Table(
    "c22_charlie_media_mvp"
)


# =========================================
# QUERY 1: Get feed metadata
# =========================================

def get_feed(feed_id: str) -> dict:
    """
    Retrieve feed by ID.
    Returns feed metadata or empty dict.
    """
    response = table.get_item(
        Key={
            "PK": f"FEED#{feed_id}",
            "SK": "META"
        }
    )
    return response.get("Item", {})


feed = get_feed("bloomberg-tech")
print(
    "QUERY 1 - Get Feed:",
    feed.get("feed_name")
)


# =========================================
# QUERY 2: Get article by ID
# =========================================

def get_article(article_id: str) -> dict:
    """
    Retrieve article metadata by ID.
    """
    response = table.get_item(
        Key={
            "PK": f"ARTICLE#{article_id}",
            "SK": "META"
        }
    )
    return response.get("Item", {})


article_id = "bloomberg-tech#guid-123"
article = get_article(article_id)
print(
    "QUERY 2 - Get Article:",
    article.get("title")
)


# =========================================
# QUERY 3: Get all mentions for a date
# =========================================

def get_mentions_by_date(
    date_str: str
) -> list:
    """
    Query all mentions for a date.
    Returns list of mention items.
    """
    response = table.query(
        KeyConditionExpression=(
            "PK = :pk"
        ),
        ExpressionAttributeValues={
            ":pk": f"MENTION_DATE#{date_str}"
        }
    )
    return response.get("Items", [])


mentions = get_mentions_by_date(
    "2026-03-18"
)
print(
    "QUERY 3 - Mentions on date:",
    len(mentions),
    "found"
)


# =========================================
# QUERY 4: Get mentions for entity
# =========================================

def get_entity_mentions(
    date_str: str,
    entity_id: str
) -> list:
    """
    Query mentions for entity on date.
    Uses begins_with on sort key.
    """
    entity_prefix = (
        f"ENTITY_TYPE#company"
        f"#ENTITY#{entity_id}"
    )
    response = table.query(
        KeyConditionExpression=(
            "PK = :pk AND "
            "begins_with(SK, :sk)"
        ),
        ExpressionAttributeValues={
            ":pk": f"MENTION_DATE#{date_str}",
            ":sk": entity_prefix
        }
    )
    return response.get("Items", [])


entity_mentions = get_entity_mentions(
    "2026-03-18",
    "openai"
)
print(
    "QUERY 4 - Entity mentions:",
    len(entity_mentions),
    "found"
)


# =========================================
# QUERY 5: Get mentions with sentiment
# =========================================

def filter_positive_mentions(
    mentions: list
) -> list:
    """
    Filter mentions by sentiment.
    Returns positive sentiment only.
    """
    return [
        m for m in mentions
        if m.get("sentiment") == "positive"
    ]


positive = filter_positive_mentions(
    entity_mentions
)
print(
    "QUERY 5 - Positive mentions:",
    len(positive),
    "found"
)


print("\nAll query tests complete ✅")
