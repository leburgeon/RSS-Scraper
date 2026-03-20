"""Pytest configuration for testing.

Handles mocking of external dependencies
to allow tests to run independently.
"""
import sys
from unittest.mock import MagicMock, patch


# Mock spacy before any imports to bypass
# Python 3.14 compatibility issues
spacy_mock = MagicMock()
spacy_mock.load = MagicMock(
    return_value=MagicMock()
)
spacy_mock.language = MagicMock()
spacy_mock.util = MagicMock()
spacy_mock.util.compile_suffix_regex = (
    MagicMock(
        return_value=MagicMock(
            search=MagicMock()
        )
    )
)

sys.modules["spacy"] = spacy_mock
sys.modules["spacy.util"] = (
    spacy_mock.util
)
sys.modules["spacy.language"] = (
    spacy_mock.language
)


def create_mock_nlp():
    """Create a mock NLP object."""
    mock_nlp = MagicMock()
    mock_nlp.add_pipe = MagicMock(
        return_value=MagicMock()
    )
    mock_nlp.pipe_names = []
    mock_nlp.tokenizer = MagicMock()
    mock_nlp.Defaults = MagicMock()
    mock_nlp.Defaults.suffixes = []
    mock_nlp.side_effect = (
        lambda text: MagicMock(ents=[])
    )
    return mock_nlp
