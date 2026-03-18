import polling_queries
import unittest
import hashlib


class TestPollingQueries():

    def test_generate_article_id(self):
        feed_id = "feed123"
        guid = "article456"
        expected_id = f"{feed_id}#{hashlib.sha256(guid.encode('utf-8')).hexdigest()}"
        assert polling_queries.generate_article_id(
            feed_id, guid) == expected_id
