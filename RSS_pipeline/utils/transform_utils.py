"""
Functions for extracting entities and
sentiments from article text via LLM.
"""

from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging
from pydantic import BaseModel
from typing import List, Literal

load_dotenv()


class EntityNamesResponse(BaseModel):
    """Schema for entity-name extraction."""
    entities: List[str]


class EntityAnalysis(BaseModel):
    """Schema for a single entity sentiment."""
    entity_name: str
    entity_type: Literal[
        "company", "person", "unknown"
    ]
    mention_count: int
    sentiment: Literal[
        "positive", "negative",
        "neutral", "unknown"
    ]


class EntityResponse(BaseModel):
    """Schema for full sentiment response."""
    entities: List[EntityAnalysis]


def _call_llm(
    prompt: str,
    schema: type,
) -> object | None:
    """
    Send a structured prompt to Gemini.
    Returns parsed response or None on error.
    """
    client = genai.Client()
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
    except Exception as e:
        logging.error(f"LLM request failed: {e}")
        return None
    return response.parsed


def extract_entities(text: str) -> List[str]:
    """
    Extract named entities (people, orgs)
    from text using the LLM.
    Preserves duplicate mentions.
    Returns empty list for empty input.
    """
    if not text:
        return []

    prompt = (
        f"Extract all named entities (people, "
        f"organisations, and notable products) "
        f"from the following text. "
        f"Preserve duplicates for each mention. "
        f"Return only a JSON list of name strings."
        f"\n\nText: {text}"
    )
    result = _call_llm(prompt, EntityNamesResponse)
    if result is None:
        return []
    return result.entities

def extract_sentiments_and_counts_per_entity(article: str, entities: list) -> dict[str:str]:
    """Extracts the sentiment for each entity mentioned in the article, alongside the count of these mentions.
    Each entry is a dictionary in the form {entity: [sentiment, count]}.
    If an entity is mentioned in a positive and negative light, two entries will be made.
    'entities' will contain duplicates and these duplicates should be removed in the analysis.
    This function uses an LLM API to analyse the sentiment of the article.
    """

    if article == "" or entities == []:
        logging.warning("Empty article or entity list provided to extract_sentiments_and_counts_per_entity.")
        return []

    prompt = f"""Given the following article, determine the sentiment of each mention of the following entities: {entities}.
        and return a dictionary in the following format.
        e.g. {{"entity_name": "OpenAI",
        "entity_type": "company",
        "mention_count": 5
        "sentiment": "positive"}}

        Article: {article}. Ensure that you capture the sentiment of each mention of the entity. 
        If an entity is mentioned in a positive and negative light, two entries should be made. 
        The same rationale is applied to neutral mentions. However, if for a single entity, there is only positive and neutral, or, negative and neutral:
        Only the positive/negative sentiments should be counted and the neutral should be ignored. The output should be in the format of a dictionary
        where the keys are the entities and the values are lists containing the sentiment and count of mentions,
        e.g. {{"entity_name": "OpenAI",
        "entity_type": "company",
        "mention_count": 5
        "sentiment": "positive"}}.
        The entity_type should be either 'company or 'person'. If you are unsure, ignore this field
        as it is likely to be inaccurate. The sentiment should be either 'positive', 'negative' or 'neutral'.
        If you are unsure, ignore this field as it is likely to be inaccurate."""


    return get_LLM_response(prompt)


def get_LLM_response(prompt: str) -> list:
    """Send prompt to Gemini; return list of
    serialised EntityAnalysis dicts.
    """
    result = _call_llm(prompt, EntityResponse)
    if result is None:
        return []
    return [
        item.model_dump()
        for item in result.entities
    ]
