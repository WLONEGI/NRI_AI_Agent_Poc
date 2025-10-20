from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from apis import query_api as module


def _agent_stub(**_: object) -> dict[str, object]:
    return {
        "answer": "Echo: hello",
        "knowledge": {
            "id": "kn-123",
            "type": "personal",
            "content": "content",
            "hierarchy_level": 1,
            "owner_id": "user-1",
            "team_id": None,
            "confidence": 0.7,
            "embedding": None,
            "created_at": "2025-10-19T00:00:00Z",
            "tags": ["agent"],
        },
        "provenance": {
            "query_id": "q-1",
            "agent_execution_id": "ae-1",
            "tool_execution_id": "te-1",
            "data_source_id": "ds-1",
            "extracted_content_id": "ec-1",
        },
        "provenance_chain": [
            {
                "id": "kn-123",
                "source_type": "agent_synthesis",
                "summary": "summary",
                "owner": {"user_id": "user-1"},
                "created_at": "2025-10-19T00:00:00Z",
            }
        ],
        "references": [
            {
                "id": "kn-123",
                "source_type": "agent_synthesis",
                "summary": "summary",
                "owner": {"user_id": "user-1"},
                "created_at": "2025-10-19T00:00:00Z",
            }
        ],
        "retries": 0,
        "tool_traces": [{"name": "langgraph.run", "input": {}, "output": {}}],
    }


def test_handle_query_persists_and_returns_response(monkeypatch: pytest.MonkeyPatch) -> None:
    repo = MagicMock()

    def fake_save(payload, repo=None, logger=None):  # noqa: ANN001
        assert payload["knowledge"]["id"] == "kn-123"
        return payload["knowledge"]["id"]

    monkeypatch.setattr(module, "save_knowledge", fake_save)

    request = module.QueryRequest(user_id="user-1", query="hello")
    query_log_repo = MagicMock()
    response = module.handle_query(
        request,
        repo=repo,
        agent_runner=_agent_stub,
        logger=MagicMock(),
        query_log_repo=query_log_repo,
    )

    assert response.knowledge_id == "kn-123"
    assert response.answer == "Echo: hello"
    assert response.references[0].source_type == "agent_synthesis"
    repo.save.assert_not_called()  # save_knowledge handles calling repo.save internally
    query_log_repo.record_query.assert_called_once()


def test_handle_query_agent_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    request = module.QueryRequest(user_id="user-1", query="hello")

    def failing_runner(**kwargs):  # noqa: ANN001
        raise RuntimeError("boom")

    with pytest.raises(HTTPException) as exc_info:
        module.handle_query(
            request,
            repo=MagicMock(),
            agent_runner=failing_runner,
            logger=MagicMock(),
            query_log_repo=MagicMock(),
        )

    assert exc_info.value.status_code == 500
