from pipeline import extract_sentiments_and_counts_per_entity


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
