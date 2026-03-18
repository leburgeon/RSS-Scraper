"""
This script is the main pipeline for RSS extraction.

This script should extract the entities from the RSS feed. 
Then it should rate these entities 'positive', 'negative' or 'neutral' based on the sentiment of the article.

If the article mentions an entity in a positive and negative light, two entries should be made.

"""

import csv
import json
import io
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import logging

from entity_extraction import extract_entities

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


def extract_sentiments_and_counts_per_entity(article:str, entities:list) -> dict[str:str]:
    """Extracts the sentiment for each entity mentioned in the article, alongside the count of these mentions.
    
    If an entity is mentioned in a positive and negative light, two entries will be made.

    'entities' will contain duplicates and these duplicates should be removed in the analysis.

    This function uses an LLM API to analyse the sentiment of the article.

    """

    prompt = f"""Given the following article, determine the sentiment of each mention of the following entities: {entities}.

Article: {article}. Ensure that you capture the sentiment of each mention of the entity. 
If an entity is mentioned in a positive and negative light, two entries should be made. 
The same rationale is applied to neutral mentions. The output should be in the format of a dictionary
where the keys are the entities and the values are lists containing the sentiment and count of mentions,
e.g. {{"Apple": ["positive", 3], "Apple": ["negative", 1]}}."""
    
    get_LLM_response(prompt)
    


def get_LLM_response(prompt:str) -> dict:

    pass