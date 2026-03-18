"""
This script contains functions for loading and preprocessing data for the RSS pipeline.
This includes functions error handling and loading data to awsDynamoDB. """


def enrich_impressions_with_article_metadata(impressions: list[dict], article: dict) -> list[dict]:
    """Enrich impressions with article metadata. This is useful for downstream processing and analysis."""
    
    for impression in impressions:
        impression['article_title'] = article.get('title')
        impression['article_link'] = article.get('link')
        impression['article_publish_date'] = article.get('publish_date')
        impression['article_guid'] = article.get('guid')
        impression['article_summary'] = article.get('summary')
    
    return impressions
