"""
All functions related to extracting entities from text should
be defined here.

This includes functions for extracting named entities, as well as all python packages."""

import spacy
from typing import List


from spacy.util import compile_suffix_regex
from spacy.language import Language



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


# nlp = setup_nlp()


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

    target_labels = {"PERSON", "ORG", "PRODUCT", "GPE"}

    entities = []
    
    for ent in doc.ents:
        if ent.label_ in target_labels:

            nnp_parts = [token.text for token in ent if token.tag_ == "NNP"]

            clean_name = " ".join(nnp_parts).strip().rstrip('.,')

            if clean_name and len(clean_name) > 3 and clean_name[0].isupper():
                entities.append(clean_name)

    return entities
    