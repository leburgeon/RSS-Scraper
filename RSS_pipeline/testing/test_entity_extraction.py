import pytest
from entity_extraction import extract_entities


class TestTechEntityExtraction:

    def test_tech_figures(self):
        """Tests major tech industry leaders."""
        text = "Jensen Huang and Mark Zuckerberg discussed the metaverse."
        expected = ["Jensen Huang", "Mark Zuckerberg"]
        assert extract_entities(text) == expected

    def test_tech_companies_and_suffixes(self):
        """Tests companies, specifically checking the trailing period issue."""
        text = "I am looking for a job at SpaceX. My friend works at Nvidia."
        expected = ["SpaceX", "Nvidia"]
        assert extract_entities(text) == expected

    def test_mixed_tech_entities(self):
        """Tests a mix of people and organizations in one sentence."""
        text = "Sundar Pichai leads Google, while Tim Cook runs Apple."
        results = extract_entities(text)
        assert set(results) == {"Sundar Pichai", "Google", "Tim Cook", "Apple"}

    def test_modern_tech_casing(self):
        """Tests specific casing for newer tech companies."""
        text = "OpenAI and Anthropic are competing in the LLM space."
        expected = ["OpenAI", "Anthropic"]
        assert extract_entities(text) == expected

    def test_repeated_tech_mentions(self):
        """Tests multiple mentions across a technical paragraph."""
        text = (
            "Satya Nadella announced a new partnership between Microsoft and several AI startups. "
            "While Satya Nadella praised the innovation, Sam Altman noted that OpenAI would remain a key collaborator. "
            "Microsoft has invested billions into the vision shared by Sam Altman. "
            "Both Microsoft and OpenAI aim to redefine the future of computing together. "
            "Ultimately, Satya Nadella believes this synergy benefits every developer."
        )

        expected = [
            "Satya Nadella", "Microsoft",
            "Satya Nadella", "Sam Altman", "OpenAI",
            "Microsoft", "Sam Altman",
            "Microsoft", "OpenAI",
            "Satya Nadella"
        ]

        assert extract_entities(text) == expected
    
    def test_empty(self):
        """Tests empty input."""
        text = "Random text with no entities."
        expected = []
        assert extract_entities(text) == expected
