from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

from knowledge.promotion_repository import PromotionRepository


def test_fetch_personal_knowledge_converts_records(monkeypatch):
    driver = MagicMock()
    driver.execute_query.return_value = (
        [
            {
                "knowledge": {"id": "kn-1"},
                "similarity": 0.82,
                "contributors": ["u1", "u2"],
                "coverage": 0.6,
            }
        ],
        None,
        None,
    )
    repo = PromotionRepository(driver)

    candidates = repo.fetch_personal_knowledge("team-1")

    driver.execute_query.assert_called_once()
    query = driver.execute_query.call_args[0][0]
    assert "BELONGS_TO" in query
    assert candidates[0]["id"] == "kn-1"
    assert candidates[0]["contributors"] == {"u1", "u2"}


def test_promote_to_team_returns_new_id(monkeypatch):
    driver = MagicMock()
    driver.execute_query.return_value = ([{"id": "team-kn-1"}], None, None)
    repo = PromotionRepository(driver)

    promoted_id = repo.promote_to_team(knowledge_id="kn-1", team_id="team-1")

    _, kwargs = driver.execute_query.call_args
    assert kwargs["knowledge_id"] == "kn-1"
    assert kwargs["team_id"] == "team-1"
    assert promoted_id == "team-kn-1"


def test_record_audit_event_executes_query(monkeypatch):
    driver = MagicMock()
    repo = PromotionRepository(driver)

    repo.record_audit_event(
        team_id="team-1",
        knowledge_id="kn-1",
        status="promoted",
        similarity=0.9,
        contributor_count=3,
        coverage=0.6,
        reason="",
        dry_run=False,
    )

    assert driver.execute_query.called
