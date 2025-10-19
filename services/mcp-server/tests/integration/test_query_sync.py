from __future__ import annotations

from unittest.mock import MagicMock

from apis.query_api import handle_query


def test_handle_query_waits_for_persistence() -> None:
    repo = MagicMock()
    repo.save.return_value = "kn-10"
    embedding_client = MagicMock()
    embedding_client.embed.return_value = [[0.1, 0.2, 0.3]]
    logger = MagicMock()

    payload = {
        "knowledge": {
            "id": "kn-10",
            "type": "personal",
            "content": "content",
            "category": "general",
            "hierarchy_level": 1,
            "owner_id": "user-1",
            "team_id": None,
            "confidence": 0.8,
            "created_at": "2025-10-17T00:00:00Z",
            "tags": [],
        },
        "provenance": {
            "query_id": "q-1",
            "agent_execution_id": "ae-1",
            "tool_execution_id": "te-1",
            "data_source_id": "ds-1",
            "extracted_content_id": "ec-1",
        },
    }

    result = handle_query(payload, repo=repo, embedding_client=embedding_client, logger=logger)

    repo.save.assert_called_once()
    assert result["knowledge_id"] == "kn-10"
