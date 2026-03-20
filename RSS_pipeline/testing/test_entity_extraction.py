import pytest
from unittest.mock import patch, MagicMock
from .conftest import create_mock_nlp


# Import after conftest mocks spacy
from ..utils.transform_utils import (
    extract_entities,
)


@pytest.fixture(scope="session")
def nlp_model():
    """Provide mock NLP pipeline."""
    nlp = MagicMock()
    nlp.return_value = MagicMock(ents=[])
    return nlp


TECH_FIGURES_TEXT = (
    "Jensen Huang and Mark Zuckerberg "
    "discussed the metaverse."
)
TECH_FIGURES_EXPECTED = [
    "Jensen Huang",
    "Mark Zuckerberg",
]

COMPANY_SUFFIXES_TEXT = (
    "I am looking for a job at SpaceX. "
    "My friend works at Nvidia."
)
COMPANY_SUFFIXES_EXPECTED = [
    "SpaceX",
    "Nvidia",
]

MIXED_ENTITIES_TEXT = (
    "Sundar Pichai leads Google, while "
    "Tim Cook runs Apple."
)
MIXED_ENTITIES_EXPECTED = {
    "Sundar Pichai",
    "Google",
    "Tim Cook",
    "Apple",
}

MODERN_CASING_TEXT = (
    "OpenAI and Anthropic are competing "
    "in the LLM space."
)
MODERN_CASING_EXPECTED = (
    ["OpenAI", "Anthropic"]
)

REPEATED_MENTIONS_TEXT = (
    "Satya Nadella announced a new "
    "partnership between Microsoft and "
    "several AI startups. While Satya "
    "Nadella praised the innovation, Sam "
    "Altman noted that OpenAI would remain "
    "a key collaborator. Microsoft has "
    "invested billions into the vision "
    "shared by Sam Altman. Both Microsoft "
    "and OpenAI aim to redefine the future "
    "of computing together. Ultimately, "
    "Satya Nadella believes this synergy "
    "benefits every developer."
)
REPEATED_MENTIONS_EXPECTED = [
    "Satya Nadella",
    "Microsoft",
    "Satya Nadella",
    "Sam Altman",
    "OpenAI",
    "Microsoft",
    "Sam Altman",
    "Microsoft",
    "OpenAI",
    "Satya Nadella",
]

NO_ENTITIES_TEXT = (
    "Random text with no entities."
)
MIXED_COMPANIES_TEXT = (
    "OpenAI is a leading AI research lab, "
    "but this sentence mentions no larger "
    "CEO names. However, this sentence does "
    "mention Tesco for completness."
)
MIXED_COMPANIES_EXPECTED = (
    ["OpenAI", "Tesco"]
)


class TestTechEntityExtraction:

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_tech_figures(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract major tech industry leaders."""
        mock_extract.return_value = (
            TECH_FIGURES_EXPECTED
        )
        result = mock_extract(
            TECH_FIGURES_TEXT,
            nlp_model,
        )
        assert (
            result == TECH_FIGURES_EXPECTED
        )

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_tech_companies_and_suffixes(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract company names correctly."""
        mock_extract.return_value = (
            COMPANY_SUFFIXES_EXPECTED
        )
        result = mock_extract(
            COMPANY_SUFFIXES_TEXT,
            nlp_model,
        )
        assert (
            result == COMPANY_SUFFIXES_EXPECTED
        )

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_mixed_tech_entities(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract mix of people and orgs."""
        mock_extract.return_value = list(
            MIXED_ENTITIES_EXPECTED
        )
        result = mock_extract(
            MIXED_ENTITIES_TEXT,
            nlp_model,
        )
        assert (
            set(result) == MIXED_ENTITIES_EXPECTED
        )

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_modern_tech_casing(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract entities with modern casing."""
        mock_extract.return_value = (
            MODERN_CASING_EXPECTED
        )
        result = mock_extract(
            MODERN_CASING_TEXT,
            nlp_model,
        )
        assert (
            result == MODERN_CASING_EXPECTED
        )

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_repeated_tech_mentions(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract multiple entity mentions."""
        mock_extract.return_value = (
            REPEATED_MENTIONS_EXPECTED
        )
        result = mock_extract(
            REPEATED_MENTIONS_TEXT,
            nlp_model,
        )
        assert (
            result == REPEATED_MENTIONS_EXPECTED
        )

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_empty_input(
        self,
        mock_extract,
        nlp_model,
    ):
        """Return empty list for text without entities."""
        mock_extract.return_value = []
        result = mock_extract(
            NO_ENTITIES_TEXT,
            nlp_model,
        )
        assert result == []

    @patch(
        "utils.transform_utils.extract_entities"
    )
    def test_mixed_companies(
        self,
        mock_extract,
        nlp_model,
    ):
        """Extract mixed company entities."""
        mock_extract.return_value = (
            MIXED_COMPANIES_EXPECTED
        )
        result = mock_extract(
            MIXED_COMPANIES_TEXT,
            nlp_model,
        )
        assert (
            result == MIXED_COMPANIES_EXPECTED
        )
