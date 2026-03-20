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
import json

load_dotenv()


def embed_user_question(user_input: str) -> list[float]:
    """Embed a chunk of text using OpenAI's embedding API."""

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
                    SELECT DISTINCT
                        chunk_text,
                        published_at,
                        chunk_embedding <=> %s::vector AS distance
                    FROM chunks
                    ORDER BY distance
                        LIMIT 10;"""

    results = execute_query(query, question_embed, conn)
    if results is None:
        return []

    return results


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


def get_openai_client(api_key: str):
    """Initializes and returns the OpenAI client."""
    try:
        ai = OpenAI(api_key=api_key)
        return ai
    except Exception as e:
        logging.error(f"Error initializing OpenAI client: {e}")
        return None


def get_llm_response(client, context_list: list[str], user_query: str) -> str:
    """
    Combines context strings into a single block, 
    runs the prompt, and returns the string response.
    """

    chunks = [
        # Extract the chunk text from the context list
        text for text, date, _ in context_list
    ]

    dates = [
        # Extract the published_at date and format it as a string
        date.strftime("%d %b %Y, %H:%M") for text, date, _ in context_list
    ]

    # Flatten the list of strings into one readable block
    formatted_text = "\n---\n".join(chunks)

    formatted_dates = "\n---\n".join(dates)

    # Construct the System and User messages
    system_prompt = (
        f"""You are working with a tech company PR team. You have been asked to answer the
        users questions using the following context below to help support your claims.
        DO NOT mention that you have access to this context, just use it to inform your answer. If you don't know the answer, say you don't know.

        When using the context, mention the date of the article you are referencing to help the user understand the timeline of events.

        The dates correspond to the order of the context text, so the first date corresponds to the first chunk of text, and so on.
        
        CONTEXT:\n{formatted_text}

        DATES: \n{formatted_dates}  """

    )

    try:
        response = client.chat.completions.create(
            model=os.getenv("GPT_MODEL"),  # Or your preferred model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error connecting to OpenAI: {str(e)}"


def send_user_input_to_llm(user_input: str) -> str:
    """Main function to be called by lambda. Takes user input, gets relevant context from RDS, and returns the LLM response."""

    question_embed = embed_user_question(user_input)

    relevant_chunks = get_relevant_chunks_from_RAG_RDS(question_embed)

    openai_client = get_openai_client(os.getenv("OPENAI_API_KEY"))

    llm_response = get_llm_response(openai_client, relevant_chunks, user_input)

    return llm_response


def lambda_handler(event, context):
    """AWS Lambda handler function."""
    user_input = event.get("question", "")
    if not user_input:
        return {
            "statusCode": 400,
            "body": "No question provided in the request."
        }

    response = send_user_input_to_llm(user_input)

    return {
        "statusCode": 200,
        "body": json.dumps({"response": response})
    }
