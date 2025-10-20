from __future__ import annotations

from unittest.mock import MagicMock

from apis import query_api as module


def _agent_stub(**_: object) -> dict[str, object]:
    return {
        "answer": "Final answer",
        "knowledge": {
            "id": "kn-10",
            "type": "personal",
            "content": "content",
            "hierarchy_level": 1,
            "owner_id": "user-1",
            "team_id": "team-1",
            "confidence": 0.9,
            "embedding": None,
            "created_at": "2025-10-19T00:00:00Z",
            "tags": ["file_search"],
        },
        "provenance": {
            "query_id": "q-1",
            "agent_execution_id": "ae-1",
            "tool_execution_id": "te-1",
            "data_source_id": "ds-1",
            "extracted_content_id": "ec-1",
        },
        "references": [
            {
                "id": "kn-20",
                "source_type": "team_knowledge",
                "summary": "ref",
            }
        ],
    }


def test_handle_query_persists_to_repo_and_logs(monkeypatch) -> None:
    repo = MagicMock()
    repo.save.return_value = "kn-10"
    query_log_repo = MagicMock()

    def fake_save(payload, repo=None, logger=None):  # noqa: ANN001
        repo.save(payload["knowledge"], payload["provenance"])
        return payload["knowledge"]["id"]

    monkeypatch.setattr(module, "save_knowledge", fake_save)

    request = module.QueryRequest(user_id="user-1", query="hello", channels=["file_search"])
    response = module.handle_query(
        request,
        repo=repo,
        agent_runner=_agent_stub,
        logger=MagicMock(),
        query_log_repo=query_log_repo,
    )

    repo.save.assert_called_once()
    query_log_repo.record_query.assert_called_once()
    assert response.knowledge_id == "kn-10"
    assert response.answer.startswith("Final answer")
