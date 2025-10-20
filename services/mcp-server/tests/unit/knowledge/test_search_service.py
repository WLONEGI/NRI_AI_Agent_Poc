from __future__ import annotations

from unittest.mock import MagicMock

from knowledge import search_service as module
from knowledge.search_service import KnowledgeSearchService
from provenance import provenance_logger


def test_search_service_returns_ranked_results(monkeypatch) -> None:
    repo = MagicMock()
    repo.find_team_ids.return_value = ["team-1"]
    repo.search_vector_index.return_value = [
        {
            "knowledge": {
                "id": "kn-1",
                "content": "some content",
                "type": "personal",
                "created_at": "2025-10-19T00:00:00Z",
                "owner_id": "user-1",
                "owner_team_id": "team-1",
            },
            "similarity": 0.92,
        }
    ]

    embedding_client = MagicMock()
    embedding_client.embed.return_value = [[0.1, 0.2, 0.3]]
    monkeypatch.setattr(module, "get_embedding_client", lambda: embedding_client)

    logged = []
    monkeypatch.setattr(
        provenance_logger,
        "log_search_provenance",
        lambda user_id, ids, query=None: logged.append((user_id, ids, query)),
    )

    log_repo = MagicMock()
    service = KnowledgeSearchService(driver=MagicMock(), repository=repo, query_log_repo=log_repo)
    results = service.search("how to", "user-1", top_k=50)

    assert results[0]["id"] == "kn-1"
    assert results[0]["summary"].startswith("some content")
    repo.search_vector_index.assert_called_with(
        embedding=[0.1, 0.2, 0.3],
        user_id="user-1",
        team_ids=["team-1"],
        top_k=50,
    )
    assert logged == [("user-1", ["kn-1"], "how to")]
    log_repo.record_search.assert_called_once_with(user_id="user-1", query="how to", knowledge_ids=["kn-1"])


def test_search_service_returns_empty_on_embedding_failure(monkeypatch) -> None:
    repo = MagicMock()
    monkeypatch.setattr(module, "get_embedding_client", lambda: MagicMock(embed=MagicMock(side_effect=RuntimeError("no"))))

    logged = []
    monkeypatch.setattr(
        provenance_logger,
        "log_search_provenance",
        lambda user_id, ids, query=None: logged.append((user_id, ids, query)),
    )

    log_repo = MagicMock()
    service = KnowledgeSearchService(driver=MagicMock(), repository=repo, query_log_repo=log_repo)
    results = service.search("query", "user-1")

    assert results == []
    repo.search_vector_index.assert_not_called()
    assert logged == [("user-1", [], "query")]
    log_repo.record_search.assert_called_once_with(user_id="user-1", query="query", knowledge_ids=[])
