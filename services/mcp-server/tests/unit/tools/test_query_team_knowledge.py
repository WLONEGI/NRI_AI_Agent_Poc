from __future__ import annotations

from unittest.mock import MagicMock

from tools import query_team_knowledge as module
from tools.query_team_knowledge import query_team_knowledge


def test_query_team_knowledge_returns_ranked_results(monkeypatch) -> None:
    driver = MagicMock()
    driver.execute_query.side_effect = [
        ([{"team_ids": ["team-1"]}], None, None),
        (
            [
                {"knowledge": {"id": "kn-1", "content": "stuff", "similarity": 0.9}},
                {"knowledge": {"id": "kn-2", "content": "other", "similarity": 0.7}},
            ],
            None,
            None,
        ),
    ]

    embedding_client = MagicMock()
    embedding_client.embed.return_value = [[0.1, 0.2, 0.3]]
    monkeypatch.setattr(module, "get_embedding_client", lambda: embedding_client)

    results = query_team_knowledge(query="crystal", user_id="user-1", driver=driver)

    assert len(results) == 2
    assert results[0]["id"] == "kn-1"
    assert driver.execute_query.call_count == 2
    embedding_client.embed.assert_called_once_with(["crystal"])


def test_query_team_knowledge_returns_empty_when_embedding_fails(monkeypatch) -> None:
    driver = MagicMock()
    monkeypatch.setattr(module, "get_embedding_client", lambda: MagicMock(embed=MagicMock(side_effect=RuntimeError("no"))))

    results = query_team_knowledge(query="crystal", user_id="user-1", driver=driver)

    assert results == []
    driver.execute_query.assert_not_called()
