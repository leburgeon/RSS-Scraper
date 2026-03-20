"""
This script contains the function that will be used by lambda in AWS.
This lambda function will take a message delivered from the streamlit frontend in the
form {"question":user_input}.

This script will take this input, embed the question, search through the RAG RDS 
for relevant chunks. Then send an api to chatgpt with the given article chunks as context.

Then the response is given back to lambda and returned to the streamlit front end by returning a json response.
"""

import os
import logging
from openai import OpenAI
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def embed_user_question(user_input: str) -> list[float]:
    """Embed a chunk of text using OpenAI's embedding API."""

    # return [0.0] * 1536  # Placeholder embedding for testing purposes

    if not isinstance(user_input, str):
        raise ValueError("chunk must be a string")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=user_input.strip(),
    )

    return response.data[0].embedding


def get_relevant_chunks_from_RAG_RDS(question_embed: list[float]) -> list[str]:
    """Search through the RAG RDS for relevant chunks based on the embedded user question.

    User nearest vector search to find the most relevant chunks, and return the text of those chunks as a list of strings."""

    with get_RDS_connection() as conn:
        if conn is None:
            return []

    query = """
                    SELECT DISTINCT content_chunk 
                    FROM rag_articles 
                    ORDER BY embedding <=> %s::vector 
                    LIMIT 5;
                """

    results = execute_query(query, question_embed, conn)
    if results is None:
        return []

    return [row[0] for row in results]


def get_RDS_connection() -> psycopg2.extensions.connection:
    """Establish a connection to the RAG RDS and return the connection object."""

    try:
        conn = psycopg2.connect(
            host=os.getenv("RDS_HOST"),
            port=os.getenv("RDS_PORT"),
            dbname=os.getenv("RDS_DB_NAME"),
            user=os.getenv("RDS_USER"),
            password=os.getenv("RDS_PASSWORD")
        )
    except psycopg2.Error as e:
        logging.error(f"Error connecting to RDS: {e}")
        return None

    return conn


def execute_query(query: str, question_embed: list[float], conn: psycopg2.extensions.connection):
    """Execute a SQL query against the RAG RDS and return the results."""

    try:
        with conn.cursor() as cursor:
            cursor.execute(query, (question_embed,))
            results = cursor.fetchall()
            return results
    except psycopg2.Error as e:
        logging.error(f"Error executing query: {e}")
        return None

if __name__ == "__main__":

    test_question = "What are the latest developments in AI?"
    question_embedding = embed_user_question(test_question)
    relevant_chunks = get_relevant_chunks_from_RAG_RDS(question_embedding)
    print("Relevant chunks from RDS:")
    for chunk in relevant_chunks:
        print(chunk)




