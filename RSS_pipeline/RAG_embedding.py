"""Functions for embedding article chunks with OpenAI and uploading data to the RAG RDS."""

import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()


def embed_chunk_via_openai(chunk: str) -> list[float]:
    """Embed a chunk of text using OpenAI's embedding API."""

    if not isinstance(chunk, str):
        raise ValueError("chunk must be a string")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=chunk.strip(),
    )

    return response.data[0].embedding


def split_article_to_chunks(article: str, chunk_size: int = 500) -> list[str]:
    """Split an article into chunks of a specified size.
    Ensures chunks overlap by a third to preserve context for embedding."""

    if article is None or article == "":
        return []

    words = article.split()

    if len(words) <= chunk_size:
        return [article]

    overlap = chunk_size // 3
    chunks = []
    i = 0

    while i < len(words):
        end = min(i + chunk_size, len(words))
        chunk = words[i:end]
        chunks.append(" ".join(chunk))

        if end == len(words):
            break

        i += chunk_size - overlap

    return chunks
