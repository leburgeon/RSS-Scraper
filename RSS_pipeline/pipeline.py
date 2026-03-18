"""
This script is the main pipeline for RSS extraction.

This script should extract the entities from the RSS feed. 
Then it should rate these entities 'positive', 'negative' or 'neutral' based on the sentiment of the article.

If the article mentions an entity in a positive and negative light, two entries should be made.

"""


from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging
from pydantic import BaseModel
from typing import List, Literal

from entity_extraction import extract_entities


class EntityAnalysis(BaseModel):
    entity_name: str
    entity_type: Literal["company", "person", "unknown"]
    mention_count: int
    sentiment: Literal["positive", "negative", "neutral", "unknown"]

class EntityResponse(BaseModel):
    entities: List[EntityAnalysis]


def set_up_logger():
    """Set up a logger for the pipeline. This logger will print messages to the console
    """

    logger = logging.getLogger("RSS_Pipeline")
    logger.setLevel(logging.DEBUG)

    # Create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    return logger


load_dotenv()


def extract_sentiments_and_counts_per_entity(article: str, entities: list) -> dict[str:str]:
    """Extracts the sentiment for each entity mentioned in the article, alongside the count of these mentions.
    Each entry is a dictionary in the form {entity: [sentiment, count]}.
    If an entity is mentioned in a positive and negative light, two entries will be made.
    'entities' will contain duplicates and these duplicates should be removed in the analysis.
    This function uses an LLM API to analyse the sentiment of the article.

    """

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


def get_LLM_response(prompt: str) -> dict:
    """Sends an LLM prompt to the Gemini API and returns the response as a dictionary."""

    client = genai.Client()

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EntityResponse,
            )
        )
    except Exception as e:
        logging.error(f"Error connecting to LLM: {e}")
        return []

    return [item.model_dump() for item in response.parsed.entities]
