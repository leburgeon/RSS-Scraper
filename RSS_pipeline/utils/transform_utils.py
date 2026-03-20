"""
Functions for extracting entities and
sentiments from article text via LLM.
"""

from dotenv import load_dotenv
from openai import OpenAI
import logging
from pydantic import BaseModel
from typing import List, Literal
import spacy
from spacy.util import compile_suffix_regex
from utils.extract_utils import Article

load_dotenv()

TECH_COMPANY_ALIASES = {
    "OpenAI": [
        "Open AI", "OPENAI", "Open-AI",
        "OpenAI Inc", "OpenAI LP"
    ],
    "Microsoft": [
        "MSFT", "MS", "Microsoft Corp",
        "Microsoft Corporation"
    ],
    "Google": [
        "Alphabet", "Google LLC",
        "Alphabet Inc", "Google Inc"
    ],
    "Anthropic": [
        "Anthropic Inc", "Anthropic PBC"
    ],
    "Tesla": [
        "TSLA", "Tesla Inc",
        "Tesla Motors"
    ],
    "Nvidia": [
        "NVDA", "Nvidia Corp",
        "Nvidia Corporation"
    ],
    "SpaceX": [
        "Space Exploration Technologies",
        "Space X", "SpaceX Inc"
    ],
    "Apple": [
        "AAPL", "Apple Inc",
        "Apple Computer"
    ],
    "Meta": [
        "Facebook", "Meta Platforms",
        "META", "F"
    ],
    "Amazon": [
        "AMZN", "Amazon.com",
        "Amazon Web Services", "AWS"
    ],
    "Amazon AWS": [
        "AWS", "Amazon Web Services",
        "Amazon Cloud"
    ],
    "Hugging Face": [
        "HuggingFace", "Hugging-Face",
        "Huggingface"
    ],
    "Stability AI": [
        "StabilityAI", "Stability-AI",
        "Stable Diffusion"
    ],
    "Cohere": [
        "Cohere Inc"
    ],
    "Databricks": [
        "Databricks Inc"
    ],
    "Scale AI": [
        "ScaleAI", "Scale-AI"
    ],
}


class EntityNamesResponse(BaseModel):
    """Schema for entity-name extraction."""
    entities: List[str]


class EntityAnalysis(BaseModel):
    """Schema for a single entity sentiment."""
    entity_name: str
    entity_type: Literal[
        "company"
    ]
    mention_count: int
    sentiment: Literal[
        "positive", "negative",
        "neutral"
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
    Send a structured prompt to OpenAI.
    Returns parsed response or None on error.
    """
    client = OpenAI()
    try:
        response = client.beta.chat.completions.parse(
            model="gpt-5-nano",
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
    except Exception as e:
        logging.error(f"LLM request failed: {e}")
        return None
    return response.choices[0].message.parsed


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
        logging.warning(
            "Empty article or entity list provided to extract_sentiments_and_counts_per_entity.")
        return []

    prompt = f"""You are an expert at identifying and analyzing 
    technology company mentions in news articles. Your task 
    is to analyze sentiment around specific company mentions 
    for a public relations intelligence tool.

    CRITICAL FILTERING RULES:
    ==========================================
    Only analyze actual technology companies. 
    You MUST REJECT:
    - Educational institutions (MIT, Stanford, 
    Berkeley, Harvard, etc.)
    - Geographic locations (San Francisco, London, 
    Beijing, Tokyo, etc.)
    - Government agencies (NSF, DARPA, NIH, etc.)
    - Generic terms ('the company', 'the firm', etc.)
    - Non-tech companies (airlines, banks, 
    restaurants, etc.)
    - Industry groups or associations

    COMPANY NORMALIZATION:
    ==========================================
    Map all entity variations to canonical 
    industry-standard names using this reference:
    {TECH_COMPANY_ALIASES}

    Examples:
    - "Open AI" → "OpenAI"
    - "MSFT" → "Microsoft"
    - "Alphabet" → "Google"
    - "Facebook" → "Meta"

    Use the most common formal name if not 
    in reference.

    SENTIMENT EXTRACTION RULES:
    ==========================================
    Count each sentiment separately. Create 
    multiple entries if an entity has different 
    sentiments.

    CRITICAL: Neutral is ONLY for genuinely 
    balanced or factual statements, NOT a 
    fallback for unclear statements.

    Neutral examples (keep these):
    - "Microsoft reported Q3 earnings."
    - "Tesla announced a new facility in Texas."
    - "Google operates in 50+ countries."
    - "Nvidia will attend industry conference."

    NOT neutral (classify as positive/negative):
    - Uncertain or unclear statements
    - Mentions without strong tone indicators
    - Ambiguous phrasing

    SENTIMENT LOGIC:
    ==========================================
    1. Normalize entity to canonical name
    2. Classify each mention as positive, 
    negative, or neutral
    3. Group by sentiment
    4. For each sentiment type with mentions, 
    create one entry with the count

    Example with multiple sentiments:
    - Entity mentioned 2x positively → one entry, 
    mention_count: 2, sentiment: "positive"
    - Entity mentioned 1x negatively → separate 
    entry, mention_count: 1, sentiment: "negative"
    - Entity mentioned 1x neutrally → separate 
    entry, mention_count: 1, sentiment: "neutral"

    REQUIRED OUTPUT FORMAT:
    ==========================================
    Return a JSON array with fields:
    - entity_name: Canonical company name
    - entity_type: Always "company"
    - mention_count: Count of this sentiment
    - sentiment: "positive", "negative", 
    or "neutral"

    EXAMPLES OF CORRECT OUTPUT:
    ==========================================
    Article: "OpenAI released GPT-5. Critics 
    raised concerns about safety. The announcement 
    was made in San Francisco."
    Output: 
    [
    {{"entity_name": "OpenAI", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "positive"}},
    {{"entity_name": "OpenAI", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "negative"}}
    ]
    (Note: San Francisco rejected, only 2 entries)

    Article: "Microsoft reported strong earnings. 
    Tesla announced production targets. Both firms 
    are growing."
    Output:
    [
    {{"entity_name": "Microsoft", 
        "entity_type": "company", 
        "mention_count": 2, 
        "sentiment": "positive"}},
    {{"entity_name": "Tesla", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "positive"}},
    {{"entity_name": "Tesla", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "neutral"}}
    ]
    (Neutral for factual statements + 
    positive implications)

    Article: "Nvidia's stock surged but faces 
    regulatory scrutiny. The company reported 
    record revenue."
    Output:
    [
    {{"entity_name": "Nvidia", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "positive"}},
    {{"entity_name": "Nvidia", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "negative"}},
    {{"entity_name": "Nvidia", 
        "entity_type": "company", 
        "mention_count": 1, 
        "sentiment": "neutral"}}
    ]

    ERRORS TO AVOID:
    ==========================================
    ❌ Including universities: 
    {{"entity_name": "MIT", ...}}
    ❌ Mapping errors: "Open AI" not "OpenAI"
    ❌ Using neutral as fallback for uncertainty
    ❌ Ignoring neutral mentions
    ❌ Undercounting mentions by combining 
    different sentiments

    NOW ANALYZE THIS ARTICLE:
    ==========================================
    Entities to analyze: {entities}

    Article text:
    {article}

    Return ONLY valid technology company 
    mentions with normalized names. If no 
    valid tech companies, return empty array []."""

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
            logging.warning(
                f"Missing expected field in LLM response item: {e}. Item: {item}")
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
