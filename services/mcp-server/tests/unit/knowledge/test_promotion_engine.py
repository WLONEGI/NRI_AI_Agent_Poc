from __future__ import annotations

from unittest.mock import MagicMock

from knowledge.promotion_engine import PromotionEngine


def test_promotion_engine_promotes_when_thresholds_met(monkeypatch):
    repository = MagicMock()
    repository.fetch_personal_knowledge.return_value = [
        {"id": "kn-1", "similarity": 0.8, "contributors": {"u1", "u2", "u3"}, "coverage": 0.6}
    ]
    engine = PromotionEngine(repository=repository)

    result = engine.run(team_id="team-1")

    assert result["promoted"][0]["knowledge_id"] == "kn-1"
    repository.promote_to_team.assert_called_with(knowledge_id="kn-1", team_id="team-1", promoted_by=None)
    repository.record_audit_event.assert_called_with(
        team_id="team-1",
        knowledge_id="kn-1",
        status="promoted",
        similarity=0.8,
        contributor_count=3,
        coverage=0.6,
        reason="",
        dry_run=False,
    )


def test_promotion_engine_skips_when_thresholds_not_met(monkeypatch):
    repository = MagicMock()
    repository.fetch_personal_knowledge.return_value = [
        {"id": "kn-2", "similarity": 0.7, "contributors": {"u1", "u2"}, "coverage": 0.4}
    ]
    engine = PromotionEngine(repository=repository)

    result = engine.run(team_id="team-1")

    assert result["promoted"] == []
    assert result["skipped"][0]["knowledge_id"] == "kn-2"
    repository.promote_to_team.assert_not_called()
    repository.record_audit_event.assert_called_with(
        team_id="team-1",
        knowledge_id="kn-2",
        status="skipped",
        similarity=0.7,
        contributor_count=2,
        coverage=0.4,
        reason="similarity_below_threshold",
        dry_run=False,
    )
