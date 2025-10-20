from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from agents import langgraph_runner as module


def _freeze_uuid(monkeypatch, values):
    iterator = iter(values)
    monkeypatch.setattr(module, "uuid4", lambda: next(iterator))


def _freeze_time(monkeypatch, iso: str) -> None:
    fake_datetime = SimpleNamespace(now=lambda tz=None: SimpleNamespace(isoformat=lambda: iso))
    monkeypatch.setattr(module, "datetime", fake_datetime)


def test_run_agent_invokes_all_tools(monkeypatch) -> None:
    file_stub = MagicMock(return_value=[{"path": "docs/a.md", "content": "alpha"}])
    web_stub = MagicMock(return_value=[{"url": "https://example.com", "content": "web"}])
    knowledge_stub = MagicMock(
        return_value=[
            {
                "id": "kn-team",
                "content": "team note",
                "type": "team",
                "owner_id": None,
                "owner_team_id": "team-1",
                "similarity": 0.87,
            }
        ]
    )

    monkeypatch.setattr(module, "file_search", file_stub)
    monkeypatch.setattr(module, "web_search", web_stub)
    monkeypatch.setattr(module, "query_team_knowledge", knowledge_stub)
    _freeze_uuid(monkeypatch, ["1", "2", "3", "4", "5", "6"])
    _freeze_time(monkeypatch, "2025-10-19T00:00:00Z")

    llm = MagicMock()
    llm.invoke.return_value = module.AIMessage(content="Onboarding answer")

    result = module.run_agent(
        query="How to onboard?",
        user_id="user-1",
        channels=["file_search", "web_search", "query_team_knowledge"],
        metadata={"team_id": "team-1"},
        attachments=[{"path": "docs/guide.pdf"}],
        llm=llm,
    )

    file_stub.assert_called_once()
    web_stub.assert_called_once_with(query="How to onboard?")
    knowledge_stub.assert_called_once_with(query="How to onboard?", user_id="user-1")
    llm.invoke.assert_called_once()

    assert result["knowledge"]["owner_id"] == "user-1"
    assert result["knowledge"]["team_id"] == "team-1"
    assert set(result["knowledge"]["tags"]) == {"file_search", "web_search", "query_team_knowledge"}
    assert result["answer"] == "Onboarding answer"

    reference_ids = {ref["id"] for ref in result["references"]}
    assert {"docs/a.md", "https://example.com", "kn-team"}.issubset(reference_ids)

    assert result["provenance_chain"][0]["id"] == result["knowledge"]["id"]
    assert len(result["tool_traces"]) == 3
