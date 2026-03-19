import boto3
from datetime import datetime, timedelta
from rss_polling import poll_rss_feed_for_articles, filter_articles_by_date, get_html_content_from_article_link, extract_article_content, generate_article_id
from rss_polling_queries import update_feed_metadata, get_most_recent_article_datetime
from entity_extraction import extract_article_content, extract_entities_and_sentiment_from_article_content


FEED_URL = "https://www.theguardian.com/technology/rss"
FEED_ID = "guardian-tech"
TABLE_NAME = "c22_rss_scraper_table"


def extract():

    articles = poll_rss_feed_for_articles(FEED_URL)

    new_articles = filter_articles_by_date(
        articles, datetime.now() - timedelta(hours=3))

    return new_articles


def transform(articles: list[dict]) -> list[dict]:
    """Extract the main content of the article from its HTML
    extract sentiment and entities from the article content
    use sentiment and article metadata to generate a list of mentions for the article

    follow this format for the entity mentions:

    {
        "PK": "MENTION_DATE#2026-03-18",
        "SK": "ENTITY_TYPE#company#ENTITY#openai#ARTICLE#guardian-tech#guid-123#SENTIMENT#positive",
        "item_type": "MENTION",

        "mention_id": "guardian-tech#guid-123#openai",

        "article_id": "guardian-tech#guid-123",
        "published_at": "Wed, 18 Mar 2026 11:00:40 GMT",

        "entity_name": "OpenAI",
        "entity_type": "company",
        "mention_count": 5

        "sentiment": "positive",

        "feed_id": "guardian-tech",

        "created_at": "2026-03-18T09:32:00Z"
    }
    """

    for article in articles:
        article_link = article.get("link")
        html_content = get_html_content_from_article_link(article_link)
        article_content = extract_article_content(html_content)


def load():
    dynamodb = boto3.resource(
        "dynamodb",
        region_name="eu-west-2"
    )

    table = dynamodb.Table(
        TABLE_NAME
    )


def main():


if __name__ == "__main__":
    main()