from ..RAG_embedding import split_article_to_chunks

ARTICLE_1_TEXT = (
    "this is a test article string to "
    "ensure split function works correctly "
    "with expected output."
)
ARTICLE_1_CHUNK_SIZE = 6
ARTICLE_1_EXPECTED_CHUNKS = [
    "this is a test article string",
    "article string to ensure split "
    "function",
    "split function works correctly with "
    "expected",
    "with expected output.",
]

ARTICLE_2_TEXT = (
    "another random article string to test "
    "the split function with a different "
    "chunk size."
)
ARTICLE_2_CHUNK_SIZE = 9
ARTICLE_2_EXPECTED_CHUNKS = [
    "another random article string to test "
    "the split function",
    "the split function with a different "
    "chunk size.",
]


def test_split_article_to_chunks_1():
    """Split article into overlapping "
    "chunks with size 6 words."""
    chunks = split_article_to_chunks(
        ARTICLE_1_TEXT,
        chunk_size=ARTICLE_1_CHUNK_SIZE,
    )
    assert chunks == ARTICLE_1_EXPECTED_CHUNKS


def test_split_article_to_chunks_2():
    """Split article into overlapping "
    "chunks with size 9 words."""
    chunks = split_article_to_chunks(
        ARTICLE_2_TEXT,
        chunk_size=ARTICLE_2_CHUNK_SIZE,
    )
    assert chunks == ARTICLE_2_EXPECTED_CHUNKS
