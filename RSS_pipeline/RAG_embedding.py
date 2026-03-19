"""Functions for embedding article chunks with OpenAI."""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def embed_chunk_via_openai(chunk: str) -> list[float]:
    """Embed a chunk of text using OpenAI's embedding API."""

    if not isinstance(chunk, str) or not chunk.strip():
        raise ValueError("chunk must be a non-empty string")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk.strip(),
    )

    return response.data[0].embedding
