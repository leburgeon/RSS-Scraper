"""
All functions related to extracting entities from text should
be defined here.

This includes functions for extracting named entities, as well as all python packages."""

import spacy
from typing import List


from spacy.util import compile_suffix_regex
from spacy.language import Language


from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging
from pydantic import BaseModel
from typing import List, Literal

from RSS_pipeline.entity_extraction_utils import extract_entities



def setup_nlp() -> spacy.language.Language:

    nlp = spacy.load("en_core_web_sm")

    # Add stricter suffix rules to prevent splitting entities like "spaceX." into "spaceX"
    suffixes = nlp.Defaults.suffixes + [r'\.$']
    suffix_re = compile_suffix_regex(suffixes)
    nlp.tokenizer.suffix_search = suffix_re.search

    # definitive company mentions.
    tech_companies = [
        "SpaceX", "Tesla", "OpenAI", "Anthropic",
        "Microsoft", "Nvidia", "Google", "Apple"
    ]

    if "entity_ruler" not in nlp.pipe_names:
        ruler = nlp.add_pipe("entity_ruler", before="ner")

        # Build patterns: we want these to be tagged as 'ORG'
        patterns = [{"label": "ORG", "pattern": name}
                    for name in tech_companies]
        ruler.add_patterns(patterns)

        patterns = [{"label": "ORG", "pattern": [{"LOWER": name.lower()}]}
                    for name in tech_companies]
        
        ruler.add_patterns(patterns)

    return nlp


nlp = setup_nlp()


def extract_entities(text: str) -> List[str]:
    """
    Extract named entities from the given text using spaCy.

    Returns a list of entity strings in order of appearance. Captures
    common named-entity labels such as PERSON and ORG. Duplicates
    (multiple mentions) are preserved.
    """
    
    if not text:
        return []

    doc = nlp(text)

    # print(f"\n--- Debugging: '{text}' ---")
    # for token in doc:
    #     print(
    #         f"Token: {token.text:10} | Tag: {token.tag_:4} | Ent: {token.ent_type_}")
    # print("-----------------------------\n")

    target_labels = {"PERSON", "ORG", "PRODUCT", "GPE"}

    entities = []
    
    for ent in doc.ents:
        if ent.label_ in target_labels:

            nnp_parts = [token.text for token in ent if token.tag_ == "NNP"]

            clean_name = " ".join(nnp_parts).strip().rstrip('.,')

            if clean_name and len(clean_name) > 3 and clean_name[0].isupper():
                entities.append(clean_name)

    return entities
    

"""
This script is the main pipeline for RSS extraction.

This script should extract the entities from the RSS feed. 
Then it should rate these entities 'positive', 'negative' or 'neutral' based on the sentiment of the article.

If the article mentions an entity in a positive and negative light, two entries should be made.

"""





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
