"""Tests for mention volume metric calculation."""

from botocore.exceptions import BotoCoreError, ClientError
import pytest
from unittest.mock import Mock, patch
import pandas as pd

from metrics import (
    filter_company_rows,
    compute_mention_volume, retrieve_dynamodb_table, mention_items_for_date)


def sample_mentions_dataframe():
    """Create a simple dataframe for testing."""
    data = [
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a1",
            "sentiment": "positive",
            "mention_count": 3
        },
        {
            "entity_name": "Apple",
            "entity_type": "company",
            "article_guid": "a2",
            "sentiment": "negative",
            "mention_count": 2
        },
        {
            "entity_name": "Amazon",
            "entity_type": "company",
            "article_guid": "a2",
            "sentiment": "negative",
            "mention_count": 2
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a1",
            "sentiment": "neutral",
            "mention_count": 1
        },
        {
            "entity_name": "Tesla",
            "entity_type": "company",
            "article_guid": "a3",
            "sentiment": "positive",
            "mention_count": 4
        },
        {
            "entity_name": "Rishi Sunak",
            "entity_type": "person",
            "article_guid": "a4",
            "sentiment": "positive",
            "mention_count": 5
        }
    ]

    return pd.DataFrame(data)


def test_create_empty_dataframe():
    """Test creating an empty dataframe with specified columns."""
    columns = ["a", "b", "c"]
    df = pd.DataFrame(columns=columns)

    assert df.empty
    assert list(df.columns) == columns


def test_filter_company_rows_only_keeps_companies():
    """Test that filtering for company rows only keeps those rows."""
    df = sample_mentions_dataframe()
    filtered_df = filter_company_rows(
        df,
        ["entity_name", "entity_type", "article_guid"],
        "Testing filter"
    )

    assert len(filtered_df) == 5
    assert all(filtered_df["entity_type"] == "company")


def test_compute_mention_volume():
    """Test that mention volume is computed correctly."""
    df = sample_mentions_dataframe()
    result_df = compute_mention_volume(df)

    apple_row = result_df[result_df["entity_name"] == "Apple"].iloc[0]
    tesla_row = result_df[result_df["entity_name"] == "Tesla"].iloc[0]

    # Apple appears in a1 and a2 only, so distinct article count = 2
    assert apple_row["mention_volume"] == 2

    # Tesla appears in a1 and a3, so distinct article count = 2
    assert tesla_row["mention_volume"] == 2


def test_compute_mention_volume_empty_dataframe():
    """Test that computing mention volume on an empty dataframe returns an empty dataframe."""
    empty_df = pd.DataFrame(
        columns=["entity_name", "entity_type", "article_guid"]
    )

    result_df = compute_mention_volume(empty_df)

    assert result_df.empty
    assert list(result_df.columns) == [
        "entity_name", "entity_type", "mention_volume"
    ]


# @patch("metrics.boto3.resource")
# def test_retrieve_dynamodb_table_success(mock_boto_resource):
#     """Test that the DynamoDB table object is returned successfully."""
#     mock_table = Mock()
#     mock_dynamodb = Mock()

#     mock_dynamodb.Table.return_value = mock_table
#     mock_boto_resource.return_value = mock_dynamodb

#     result = retrieve_dynamodb_table("test-table", "eu-west-2")

#     mock_boto_resource.assert_called_once_with(
#         "dynamodb", region_name="eu-west-2")
#     mock_dynamodb.Table.assert_called_once_with("test-table")
#     assert result == mock_table


# @patch("metrics.boto3.resource")
# def test_retrieve_dynamodb_table_client_error(mock_boto_resource):
#     """Test that ClientError is raised if boto3 resource fails."""
#     error_response = {
#         "Error": {
#             "Code": "ResourceNotFoundException",
#             "Message": "Requested resource not found"
#         }
#     }

#     mock_boto_resource.side_effect = ClientError(
#         error_response, "DescribeTable")

#     with pytest.raises(ClientError):
#         retrieve_dynamodb_table("bad-table", "eu-west-2")


# @patch("metrics.boto3.resource")
# def test_retrieve_dynamodb_table_botocore_error(mock_boto_resource):
#     """Test that BotoCoreError is raised if boto3 resource fails."""
#     mock_boto_resource.side_effect = BotoCoreError()

#     with pytest.raises(BotoCoreError):
#         retrieve_dynamodb_table("test-table", "eu-west-2")


# def test_mention_items_for_date_single_page():
#     """Test mention_items_for_date when only one query page is returned."""
#     mock_table = Mock()

#     mock_table.query.return_value = {
#         "Items": [
#             {"PK": "MENTION_DATE#2026-03-18", "entity_name": "OpenAI"},
#             {"PK": "MENTION_DATE#2026-03-18", "entity_name": "Google"}
#         ]
#     }

#     result = mention_items_for_date(mock_table, "2026-03-18")

#     assert len(result) == 2
#     assert result[0]["entity_name"] == "OpenAI"
#     assert result[1]["entity_name"] == "Google"
#     assert mock_table.query.call_count == 1


# def test_mention_items_for_date_multiple_pages():
#     """Test mention_items_for_date when query pagination is needed."""
#     mock_table = Mock()

#     first_response = {
#         "Items": [
#             {"PK": "MENTION_DATE#2026-03-18", "entity_name": "OpenAI"}
#         ],
#         "LastEvaluatedKey": {"PK": "next-page"}
#     }

#     second_response = {
#         "Items": [
#             {"PK": "MENTION_DATE#2026-03-18", "entity_name": "Google"}
#         ]
#     }

#     mock_table.query.side_effect = [first_response, second_response]

#     result = mention_items_for_date(mock_table, "2026-03-18")

#     assert len(result) == 2
#     assert result[0]["entity_name"] == "OpenAI"
#     assert result[1]["entity_name"] == "Google"
#     assert mock_table.query.call_count == 2


# def test_mention_items_for_date_client_error():
#     """Test that ClientError is raised if query fails."""
#     mock_table = Mock()

#     error_response = {
#         "Error": {
#             "Code": "ProvisionedThroughputExceededException",
#             "Message": "Throughput exceeded"
#         }
#     }

#     mock_table.query.side_effect = ClientError(error_response, "Query")

#     with pytest.raises(ClientError):
#         mention_items_for_date(mock_table, "2026-03-18")


# def test_mention_items_for_date_botocore_error():
#     """Test that BotoCoreError is raised if query fails."""
#     mock_table = Mock()
#     mock_table.query.side_effect = BotoCoreError()

#     with pytest.raises(BotoCoreError):
#         mention_items_for_date(mock_table, "2026-03-18")
