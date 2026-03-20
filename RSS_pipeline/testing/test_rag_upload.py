from RAG_embedding import split_article_to_chunks


def test_split_article_to_chunks_1():
    article = """this is a test article string to ensure split function works correctly with expected
    output."""

    chunks = split_article_to_chunks(article, chunk_size=6)

    expected_chunks = ["this is a test article string",
                          "article string to ensure split function",
                            "split function works correctly with expected",
                       "with expected output."]
    
    assert chunks == expected_chunks

def test_split_article_to_chunks_2():
    article = """another random article string 
    to test the split function with a different chunk size."""

    chunks = split_article_to_chunks(article, chunk_size=9)

    expected_chunks = ["another random article string to test the split function",
                       "the split function with a different chunk size."]

    assert chunks == expected_chunks

