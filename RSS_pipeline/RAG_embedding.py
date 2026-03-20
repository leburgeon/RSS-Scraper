"""Functions for embedding article chunks with OpenAI and uploading data to the RAG RDS."""

import os

from dotenv import load_dotenv
from openai import OpenAI

import logging

from utils.transform_utils import extract_entities, setup_nlp
from utils.extract_utils import Article
from datetime import datetime
import psycopg2


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class RAGArticleChunk:
    """A class representing a chunk of an article, its embedding, and associated metadata."""

    def __init__(self, article_guid: str, chunk_text: str, article_date: datetime):

        self.article_id = article_guid
        self.text = chunk_text
        self.embedding = embed_chunk_via_openai(chunk_text)
        self.entity_names = extract_entities(chunk_text, setup_nlp())
        self.published_at = article_date

    def upload_to_RDS(self, conn: psycopg2.extensions.connection):
        """Upload the article chunk and its metadata to the RAG RDS."""

        insert_query = """
                INSERT INTO chunks (chunk_text, chunk_embedding, entity_names, article_id, published_at)
                VALUES (%s, %s, %s, %s, %s)
                """

        if conn is None:
            logging.error("Failed to connect to RDS. Cannot upload chunk.")
            return

        self.execute_query(insert_query, conn)

    def execute_query(self, insert_query: str, conn: psycopg2.extensions.connection):
        """Execute the SQL insert query to upload the chunk data to RDS."""

        with conn.cursor() as cursor:
            try:
                cursor.execute(insert_query, (
                    self.text,
                    self.embedding,
                    self.entity_names,
                    self.article_id,
                    self.published_at
                ))
                conn.commit()
                logging.info(
                    f"Successfully uploaded chunk for article {self.article_id} to RDS.")
            except Exception as e:
                conn.rollback()
                logging.error(f"Error uploading chunk to RDS: {e}")
                logging.info("Connection rolled back.")


def get_RDS_connection() -> psycopg2.extensions.connection:
    """Establish a connection to the RAG RDS using psycopg2."""

    try:
        conn = psycopg2.connect(
            host=os.getenv("RDS_HOST"),
            port=os.getenv("RDS_PORT"),
            dbname=os.getenv("RDS_DB_NAME"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD")
        )
        logging.info("Successfully connected to RDS.")

    except psycopg2.Error as e:
        logging.error(f"Error connecting to RDS: {e}")
        return None

    return conn


def embed_chunk_via_openai(chunk: str) -> list[float]:
    """Embed a chunk of text using OpenAI's embedding API."""

    # return [0.0] * 1536  # Placeholder embedding for testing purposes

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


def upload_articles_to_RAG_RDS(articles: list[Article]):
    """Upload all article's content and metadata to the RAG RDS."""

    with get_RDS_connection() as conn:

        for article in articles:
            upload_article_to_RAG_RDS(article, conn)


def upload_article_to_RAG_RDS(article: Article, conn: psycopg2.extensions.connection):
    """Upload an article's content and metadata to the RAG RDS."""

    if article.article_content is None:
        logging.warning(
            f"Article {article.article_guid} has no content. Skipping upload.")
        return

    chunks = split_article_to_chunks(article.article_content)

    if conn is None:
        return

    for chunk in chunks:

        rag_chunk = RAGArticleChunk(
            article_guid=article.article_guid,
            chunk_text=chunk,
            article_date=article.published_at
        )
        rag_chunk.upload_to_RDS(conn)


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


if __name__ == "__main__":
    # Example usage

    pass
