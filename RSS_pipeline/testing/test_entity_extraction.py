from entity_extraction import extract_entities


import pytest

# Assuming your function is in entity_utils.py
# from entity_utils import extract_entities


class TestExtractEntities:

    # Simple Entity Extraction
    def test_simple_person_extraction(self):
        """Tests clear, single person name in a basic sentence."""
        text = "Alice Smith went to the park."
        expected = ["Alice Smith"]
        assert extract_entities(text) == expected

    def test_simple_company_extraction(self):
        """Tests clear, single company name."""
        text = "I have a meeting at Google today."
        expected = ["Google"]
        assert extract_entities(text) == expected

    def test_multiple_entities_mixed_types(self):
        """Tests multiple entities across different categories."""
        text = "Elon Musk works at Tesla and SpaceX."
        results = extract_entities(text)
        assert set(results) == {"Elon Musk", "Tesla", "SpaceX"}

    def test_multiple_sentences(self):
        """Tests extraction across a multi-sentence paragraph."""
        text = "Satya Nadella is the CEO of Microsoft. He succeeded Steve Ballmer."
        expected = ["Satya Nadella", "Microsoft", "Steve Ballmer"]
        assert extract_entities(text) == expected

    @pytest.mark.parametrize("text,expected", [
        (
            "Apple is releasing a new iPhone, but I prefer eating an apple.",
            ["Apple"]  # Should distinguish between the company and the fruit
        ),
        (
            "International Business Machines is often called IBM in the news.",
            ["International Business Machines", "IBM"]
        ),
        (
            "Amazon announced new jobs. The Amazon rainforest is beautiful.",
            ["Amazon", "Amazon"]
        )
    ])
    def test_contextual_variations(self, text, expected):
        """Tests if the function handles the same word in different contexts."""
        assert extract_entities(text) == expected

    def test_different_spellings_and_casing(self):
        """Tests resilience to inconsistent naming and casing."""
        text = "The wal-mart store is huge. I usually shop at Walmart or WalMart."
        results = extract_entities(text)
        assert "wal-mart" in [r.lower() for r in results]
        assert "walmart" in [r.lower() for r in results]
