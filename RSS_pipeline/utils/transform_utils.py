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
import spacy
from spacy.util import compile_suffix_regex
from utils.extract_utils import Article

load_dotenv()


class EntityNamesResponse(BaseModel):
    """Schema for entity-name extraction."""
    entities: List[str]


class EntityAnalysis(BaseModel):
    """Schema for a single entity sentiment."""
    entity_name: str
    entity_type: Literal[
        "company", "person"
    ]
    mention_count: int
    sentiment: Literal[
        "positive", "negative",
        "neutral", "unknown"
    ]


class EntityResponse(BaseModel):
    """Schema for full sentiment response."""
    entities: List[EntityAnalysis]


class EntityMention:
    """Class representing an entity mention extracted from the article content, enriched with article metadata."""
    def __init__(self, entity_name: str, entity_type: str, mention_count: int, sentiment: str):
        self.entity_name = entity_name
        self.entity_type = entity_type
        self.mention_count = mention_count
        self.sentiment = sentiment
        self.item_type = "MENTION"

    def enrich_with_article_metadata(self, article: Article):
        """Enrich entity with article metadata. This is useful for downstream processing and analysis."""
        self.pk = f"MENTION_DATE#{article.published_at.date().isoformat()}"
        self.sk = f"ENTITY_NAME#{self.entity_name}#ARTICLE_GUID#{article.article_guid}#SENTIMENT#{self.sentiment}"
        self.article_publish_date = article.published_at
        self.article_guid = article.article_guid

    def to_item_format(self) -> dict:
        """Convert the EntityMention object to a dictionary format suitable for database insertion."""
        return {
            "PK": self.pk,
            "SK": self.sk,
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "mention_count": self.mention_count,
            "sentiment": self.sentiment,
            "published_at": self.article_publish_date.isoformat(),
            "article_guid": self.article_guid,
            "item_type": self.item_type
        }
    
    @staticmethod
    def enrich_entity_mentions_with_article_metadata(entity_mentions: list["EntityMention"], article: Article) -> list["EntityMention"]:
        """ Enrich the extracted entity mentions with article metadata for downstream processing and analysis."""
        for entity in entity_mentions:
            entity.enrich_with_article_metadata(article)
        return entity_mentions
    

def _call_llm(prompt: str, schema: type) -> object | None:
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


def setup_nlp() -> spacy.language.Language:
    """Set up the spaCy NLP pipeline with custom entity recognition rules."""

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




def extract_entities(text: str, nlp) -> List[str]:
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

    target_labels = {"ORG", "PRODUCT"}

    entities = []
    
    for ent in doc.ents:
        if ent.label_ in target_labels:

            nnp_parts = [token.text for token in ent if token.tag_ == "NNP"]

            clean_name = " ".join(nnp_parts).strip().rstrip('.,')

            if clean_name and len(clean_name) > 3 and clean_name[0].isupper():
                entities.append(clean_name)

    return entities

def extract_sentiments_and_counts_per_entity(article: str, entities: list) -> list[EntityMention]:
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
        The sentiment should be either 'positive', 'negative' or 'neutral'.
        If you are unsure, ignore this field as it is likely to be inaccurate."""


    llm_response = get_LLM_response(prompt)

    return extract_entity_mentions_from_llm_response(llm_response)

def extract_entity_mentions_from_llm_response(llm_response: list[dict]) -> list[EntityMention]:
    """Convert LLM response to list of EntityMention objects."""
    entity_mentions = []
    for item in llm_response:
        try:
            entity_mention = EntityMention(
                entity_name=item['entity_name'],
                entity_type=item['entity_type'],
                mention_count=item['mention_count'],
                sentiment=item.get('sentiment', 'unknown')
            )
            entity_mentions.append(entity_mention)
        except KeyError as e:
            logging.warning(f"Missing expected field in LLM response item: {e}. Item: {item}")
            continue
    return entity_mentions

def get_LLM_response(prompt: str) -> list[dict]:
    """Send prompt to Gemini; return list of serialised EntityAnalysis dicts.
    """
    result = _call_llm(prompt, EntityResponse)
    if result is None:
        return []
    return [
        item.model_dump()
        for item in result.entities
    ]
