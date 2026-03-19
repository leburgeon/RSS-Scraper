from RSS_pipeline.utils.transform_utils import (
    extract_sentiments_and_counts_per_entity,
    extract_entities,
)


def test_extract_sentiments_and_counts_per_entity():
    article = """Apple's new iPhone has received positive reviews,
    but some users have reported negative experiences with the battery life.
      Overall, the product is seen as a significant improvement over previous models."""
    
    entities = ["Apple"]

    result = extract_sentiments_and_counts_per_entity(article, entities)

    expected_result = [
        {"entity_name": "Apple",
         "entity_type": "company",
         "mention_count": 2,
         "sentiment": "positive"},
        {"entity_name": "Apple",
         "entity_type": "company",
         "mention_count": 1,
            "sentiment": "negative"}
    ]
    assert result == expected_result

def test_extract_sentiments_and_counts_per_entity_neutral():
    article = """Microsoft's latest update has been released."""
    
    entities = ["Microsoft"]

    result = extract_sentiments_and_counts_per_entity(article, entities)

    expected_result = [
        {"entity_name": "Microsoft",
         "entity_type": "company",
         "mention_count": 1,
         "sentiment": "neutral"}
    ]
    assert result == expected_result

def test_extract_sentiments_and_counts_per_entity_multiple_entities():

    article = """Google and Apple are both tech giants. 
    Google's latest product has received really impressive reviews, 
    while Apple's new release has been criticized for its high price."""

    entities = ["Google", "Apple"]

    result = extract_sentiments_and_counts_per_entity(article, entities)
    expected_result = [
        {"entity_name": "Google",
         "entity_type": "company",
         "mention_count": 1,
         "sentiment": "positive"},
        {"entity_name": "Apple",
         "entity_type": "company",
         "mention_count": 1,
         "sentiment": "negative"}
    ]
    assert result == expected_result

def test_entity_extraction_and_sentiment_analysis_integration():
    article = """Elon Musk's SpaceX has been making brilliant headlines with its wildly successful rocket launches. 
    However, some critics have expressed concerns about the environmental impact of these launches."""

    entities = extract_entities(article)

    result = extract_sentiments_and_counts_per_entity(article, entities)
    expected_result = [
        {"entity_name": "Elon Musk",
         "entity_type": "person",
         "mention_count": 1,
         "sentiment": "positive"},
        {"entity_name": "SpaceX",
         "entity_type": "company",
         "mention_count": 1,
         "sentiment": "positive"},
        {"entity_name": "SpaceX",
         "entity_type": "company",
         "mention_count": 1,
         "sentiment": "negative"}
    ]
    assert result == expected_result


def test_entity_extraction_and_sentiment_analysis_integration_no_info():

    article = """The new software update has been released."""
    entities = extract_entities(article)

    result = extract_sentiments_and_counts_per_entity(article, entities)
    expected_result = []
    assert result == expected_result

def test_extract_sentiments_and_counts_per_entity_irrelevant_entities():

    article = """The new software update has been released."""
    entities = ["Apple", "Google"]

    result = extract_sentiments_and_counts_per_entity(article, entities)
    expected_result = []
    assert result == expected_result

