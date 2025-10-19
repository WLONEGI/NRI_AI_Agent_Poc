from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from knowledge.models import KnowledgeRecord
from tools.save_knowledge import save_knowledge


@pytest.fixture
def sample_payload() -> dict[str, object]:
    return {
        "knowledge": {
            "id": "kn-1",
            "type": "personal",
            "content": "hello",
            "category": "general",
            "hierarchy_level": 1,
            "owner_id": "user-1",
            "team_id": None,
            "confidence": 0.9,
            "created_at": "2025-10-17T00:00:00Z",
            "tags": ["demo"],
        },
        "provenance": {
            "query_id": "q-1",
            "agent_execution_id": "ae-1",
            "tool_execution_id": "te-1",
            "data_source_id": "ds-1",
            "extracted_content_id": "ec-1",
        },
    }


def test_save_knowledge_generates_embeddings_and_persists(sample_payload: dict[str, object]) -> None:
    repo = MagicMock()
    repo.save.return_value = "kn-1"
    embedding_client = MagicMock()
    embedding_client.embed.return_value = [[0.1, 0.2, 0.3]]
    logger = MagicMock()

    result = save_knowledge(sample_payload, repo=repo, embedding_client=embedding_client, logger=logger)

    repo.save.assert_called_once()
    saved_record: KnowledgeRecord = repo.save.call_args[0][0]
    assert saved_record.embedding == [0.1, 0.2, 0.3]
    assert result == "kn-1"


def test_save_knowledge_handles_embedding_failure(sample_payload: dict[str, object]) -> None:
    repo = MagicMock()
    repo.save.return_value = "kn-1"
    embedding_client = MagicMock()
    embedding_client.embed.side_effect = RuntimeError("boom")
    logger = MagicMock()

    result = save_knowledge(sample_payload, repo=repo, embedding_client=embedding_client, logger=logger)

    repo.save.assert_called_once()
    saved_record: KnowledgeRecord = repo.save.call_args[0][0]
    assert saved_record.embedding is None
    logger.warning.assert_called()
    assert result == "kn-1"
