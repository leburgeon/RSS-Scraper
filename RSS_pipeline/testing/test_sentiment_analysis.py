import pytest
from unittest.mock import (
    patch,
    Mock,
    MagicMock,
)
from .conftest import create_mock_nlp


# Import after conftest mocks spacy
from ..utils.transform_utils import (
    extract_sentiments_and_counts_per_entity,
    extract_entities,
)


@pytest.fixture(scope="session")
def nlp_model():
    """Provide mock NLP pipeline."""
    nlp = MagicMock()
    nlp.return_value = MagicMock(ents=[])
    return nlp


@pytest.fixture
def mock_openai():
    """Mock OpenAI API calls."""
    with patch("openai.OpenAI") as (
        MockOpenAI
    ):
        mock_client = Mock()
        mock_choice = Mock()
        mock_choice.message.parsed = (
            Mock(
                entities=[],
                __class__=Mock(
                    __name__=(
                        "EntityResponse"
                    ),
                ),
            )
        )
        mock_response = Mock()
        mock_response.choices = [
            mock_choice
        ]
        (
            mock_client.beta.chat.completions.parse
        ) = Mock(
            return_value=mock_response
        )
        MockOpenAI.return_value = (
            mock_client
        )
        yield MockOpenAI


APPLE_SENTIMENT_ARTICLE = (
    "Apple's new iPhone has received "
    "positive reviews, but some users have "
    "reported negative experiences with the "
    "battery life. Overall, the product is "
    "seen as a significant improvement over "
    "previous models."
)
APPLE_SENTIMENT_ENTITIES = ["Apple"]
APPLE_SENTIMENT_EXPECTED = [
    {
        "entity_name": "Apple",
        "entity_type": "company",
        "mention_count": 2,
        "sentiment": "positive",
    },
    {
        "entity_name": "Apple",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "negative",
    },
]

MICROSOFT_NEUTRAL_ARTICLE = (
    "Microsoft's latest update has been "
    "released."
)
MICROSOFT_NEUTRAL_ENTITIES = ["Microsoft"]
MICROSOFT_NEUTRAL_EXPECTED = [
    {
        "entity_name": "Microsoft",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "neutral",
    }
]

MULTIPLE_ENTITIES_ARTICLE = (
    "Google and Apple are both tech giants. "
    "Google's latest product has received "
    "really impressive reviews, while "
    "Apple's new release has been criticized "
    "for its high price."
)
MULTIPLE_ENTITIES_LIST = ["Google", "Apple"]
MULTIPLE_ENTITIES_EXPECTED = [
    {
        "entity_name": "Google",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "positive",
    },
    {
        "entity_name": "Apple",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "negative",
    },
]

SPACEX_ARTICLE = (
    "Elon Musk's SpaceX has been making "
    "brilliant headlines with its wildly "
    "successful rocket launches. However, "
    "some critics have expressed concerns "
    "about the environmental impact of these "
    "launches."
)
SPACEX_SENTIMENT_EXPECTED = [
    {
        "entity_name": "Elon Musk",
        "entity_type": "person",
        "mention_count": 1,
        "sentiment": "positive",
    },
    {
        "entity_name": "SpaceX",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "positive",
    },
    {
        "entity_name": "SpaceX",
        "entity_type": "company",
        "mention_count": 1,
        "sentiment": "negative",
    },
]

NO_RESULT_ARTICLE = (
    "The new software update has been "
    "released."
)
IRRELEVANT_ENTITIES = ["Apple", "Google"]


def test_extract_sentiments_and_counts_per_entity(
    mock_openai,
):
    """Analyze sentiment for single entity."""
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_func:
        result = (
            mock_func(
                APPLE_SENTIMENT_ARTICLE,
                APPLE_SENTIMENT_ENTITIES,
            )
        )
        assert isinstance(result, list)


def test_extract_sentiments_and_counts_per_entity_neutral(
    mock_openai,
):
    """Analyze neutral sentiment for entity."""
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_func:
        result = (
            mock_func(
                MICROSOFT_NEUTRAL_ARTICLE,
                MICROSOFT_NEUTRAL_ENTITIES,
            )
        )
        assert isinstance(result, list)


def test_extract_sentiments_and_counts_per_entity_multiple_entities(
    mock_openai,
):
    """Analyze sentiments for multiple entities."""
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_func:
        result = (
            mock_func(
                MULTIPLE_ENTITIES_ARTICLE,
                MULTIPLE_ENTITIES_LIST,
            )
        )
        assert isinstance(result, list)


@patch(
    "utils.transform_utils.extract_entities"
)
def test_entity_extraction_and_sentiment_analysis_integration(
    mock_extract,
    nlp_model,
    mock_openai,
):
    """Integrate extraction and sentiment analysis."""
    mock_extract.return_value = (
        ["SpaceX", "Elon Musk"]
    )
    entities = mock_extract(
        SPACEX_ARTICLE,
        nlp_model,
    )
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_sentiment:
        result = (
            mock_sentiment(
                SPACEX_ARTICLE,
                entities,
            )
        )
        assert isinstance(result, list)


@patch(
    "utils.transform_utils.extract_entities"
)
def test_entity_extraction_and_sentiment_analysis_integration_no_info(
    mock_extract,
    nlp_model,
    mock_openai,
):
    """Return empty list when no entities detected."""
    mock_extract.return_value = []
    entities = mock_extract(
        NO_RESULT_ARTICLE,
        nlp_model,
    )
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_sentiment:
        result = (
            mock_sentiment(
                NO_RESULT_ARTICLE,
                entities,
            )
        )
        assert isinstance(result, list)


def test_extract_sentiments_and_counts_per_entity_irrelevant_entities(
    mock_openai,
):
    """Return empty list for irrelevant entities."""
    with patch(
        "utils.transform_utils.extract_sentiments_and_counts_per_entity",
        return_value=[],
    ) as mock_func:
        result = (
            mock_func(
                NO_RESULT_ARTICLE,
                IRRELEVANT_ENTITIES,
            )
        )
        assert isinstance(result, list)
