import boto3
from datetime import datetime

dynamodb = boto3.resource(
    "dynamodb",
    region_name="eu-west-2"
)

table = dynamodb.Table("c22_charlie_media_mvp")

print("Connected to table:", table.table_name)


# --- Common timestamp ---
now = datetime.now().isoformat()

# =========================================
# 1. FEED ITEM
# =========================================

feed_item = {
    "PK": "FEED#bloomberg-tech",
    "SK": "META",
    "item_type": "FEED",

    "feed_id": "bloomberg-tech",
    "feed_name": "Bloomberg Technology",
    "feed_url": "https://example.com/rss",

    "etag": "W/\"test-etag-123\"",
    "last_modified": "Tue, 18 Mar 2026 09:00:00 GMT",

    "created_at": now
}

table.put_item(Item=feed_item)
print("Inserted FEED item")


# =========================================
# 2. ARTICLE ITEM
# =========================================

article_id = "bloomberg-tech#guid-123"

article_item = {
    "PK": f"ARTICLE#{article_id}",
    "SK": "META",
    "item_type": "ARTICLE",

    "article_id": article_id,
    "feed_id": "bloomberg-tech",

    "rss_guid": "guid-123",
    "article_url": "https://example.com/article-123",
    "title": "OpenAI expands enterprise offering",

    "published_at": "2026-03-18T09:30:00Z",
    "article_date": "2026-03-18",

    "extraction_status": "extracted",

    "created_at": now
}

table.put_item(Item=article_item)
print("Inserted ARTICLE item")


# =========================================
# 3. MENTION ITEM
# =========================================

mention_item = {
    "PK": "MENTION_DATE#2026-03-18",
    "SK": f"ENTITY_TYPE#company#ENTITY#openai#ARTICLE#{article_id}",
    "item_type": "MENTION",

    "mention_id": f"{article_id}#openai",

    "article_id": article_id,
    "article_date": "2026-03-18",
    "published_at": "2026-03-18T09:30:00Z",

    "entity_id": "openai",
    "entity_name": "OpenAI",
    "entity_type": "company",

    "sentiment": "positive",

    "feed_id": "bloomberg-tech",

    "created_at": now
}

table.put_item(Item=mention_item)
print("Inserted MENTION item")


print("All test inserts complete ✅")
