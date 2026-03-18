"""
All functions related to extracting entities from text should
be defined here.

This includes functions for extracting named entities, as well as all python packages."""

import spacy
from typing import List


from spacy.util import compile_suffix_regex


def setup_nlp() -> spacy.language.Language:

    nlp = spacy.load("en_core_web_sm")

    suffixes = nlp.Defaults.suffixes + [r'\.$']
    suffix_re = compile_suffix_regex(suffixes)
    nlp.tokenizer.suffix_search = suffix_re.search

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

    target_labels = {"PERSON", "ORG", "GPE", "LOC", "PRODUCT"}

    entities = []
    for ent in doc.ents:
        if ent.label_ in target_labels:
            entities.append(ent.text)

    return entities
    