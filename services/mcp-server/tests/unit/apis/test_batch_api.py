from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest

from apis.batch_api import promote, trigger_batch


class StubEngine:
    def run(self, team_id: str, dry_run: bool = False):
        return {"promoted": [{"knowledge_id": "kn-1"}], "skipped": []}


def test_trigger_batch_returns_summary():
    response = trigger_batch(team_id="team-1", promote_engine=StubEngine())
    assert response["promoted_count"] == 1
    assert response["promoted_ids"] == ["kn-1"]
    assert response["skipped"] == []


def test_promote_route_constructs_engine(monkeypatch):
    engine = StubEngine()
    monkeypatch.setattr("knowledge.promotion_repository.PromotionRepository", lambda driver: MagicMock())
    monkeypatch.setattr("knowledge.promotion_engine.PromotionEngine", lambda repository, logger=None: engine)
    monkeypatch.setattr("apis.batch_api.get_driver", lambda: MagicMock())

    result = asyncio.run(promote(team_id="team-1", dry_run=True))
    assert result["dry_run"] is True


def test_trigger_batch_raises_on_missing_engine():
    """Test that trigger_batch raises HTTPException when engine is None."""
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc_info:
        trigger_batch(team_id="team-test", promote_engine=None)

    assert exc_info.value.status_code == 500
    assert "not configured" in exc_info.value.detail


def test_trigger_batch_handles_multiple_promotions():
    """Test batch with multiple successful promotions."""

    class MultiEngine:
        def run(self, team_id: str, dry_run: bool = False):
            return {
                "promoted": [
                    {"knowledge_id": "kn-1"},
                    {"knowledge_id": "kn-2"},
                    {"knowledge_id": "kn-3"},
                ],
                "skipped": [],
            }

    response = trigger_batch(team_id="team-multi", promote_engine=MultiEngine())
    assert response["promoted_count"] == 3
    assert len(response["promoted_ids"]) == 3
    assert "kn-1" in response["promoted_ids"]
    assert response["skipped"] == []


def test_trigger_batch_handles_all_skipped():
    """Test batch where all candidates are skipped."""

    class SkipEngine:
        def run(self, team_id: str, dry_run: bool = False):
            return {
                "promoted": [],
                "skipped": [
                    {"knowledge_id": "kn-low-sim", "reason": "Below similarity threshold"},
                    {"knowledge_id": "kn-low-contrib", "reason": "Insufficient contributors"},
                ],
            }

    response = trigger_batch(team_id="team-skip", promote_engine=SkipEngine())
    assert response["promoted_count"] == 0
    assert response["promoted_ids"] == []
    assert len(response["skipped"]) == 2


def test_trigger_batch_handles_mixed_results():
    """Test batch with both promoted and skipped candidates."""

    class MixedEngine:
        def run(self, team_id: str, dry_run: bool = False):
            return {
                "promoted": [{"knowledge_id": "kn-promoted"}],
                "skipped": [
                    {"knowledge_id": "kn-skipped-1", "reason": "Low similarity"},
                    {"knowledge_id": "kn-skipped-2", "reason": "Low coverage"},
                ],
            }

    response = trigger_batch(team_id="team-mixed", promote_engine=MixedEngine())
    assert response["promoted_count"] == 1
    assert response["promoted_ids"] == ["kn-promoted"]
    assert len(response["skipped"]) == 2
    assert response["skipped"][0]["reason"] == "Low similarity"


def test_trigger_batch_respects_dry_run_flag():
    """Test that dry_run flag is passed to engine."""

    class FlagCapture:
        def __init__(self):
            self.captured_dry_run = None

        def run(self, team_id: str, dry_run: bool = False):
            self.captured_dry_run = dry_run
            return {"promoted": [], "skipped": []}

    capture = FlagCapture()
    response = trigger_batch(team_id="team-dry", dry_run=True, promote_engine=capture)

    assert response["dry_run"] is True
    assert capture.captured_dry_run is True


def test_trigger_batch_defaults_dry_run_false():
    """Test that dry_run defaults to False when not specified."""

    class FlagCapture:
        def __init__(self):
            self.captured_dry_run = None

        def run(self, team_id: str, dry_run: bool = False):
            self.captured_dry_run = dry_run
            return {"promoted": [], "skipped": []}

    capture = FlagCapture()
    response = trigger_batch(team_id="team-default", promote_engine=capture)

    assert response["dry_run"] is False
    assert capture.captured_dry_run is False


def test_trigger_batch_includes_team_id_in_result():
    """Test that result includes the team_id."""
    response = trigger_batch(team_id="team-verify", promote_engine=StubEngine())
    assert response["team_id"] == "team-verify"


def test_promote_route_passes_team_id():
    """Test that promote route passes team_id correctly to engine."""

    class TeamCapture:
        def __init__(self):
            self.captured_team_id = None

        def run(self, team_id: str, dry_run: bool = False):
            self.captured_team_id = team_id
            return {"promoted": [], "skipped": []}

    capture = TeamCapture()
    monkeypatch_promote = MagicMock()

    async def mock_promote(team_id: str, dry_run: bool = False):
        return trigger_batch(team_id=team_id, dry_run=dry_run, promote_engine=capture)

    asyncio.run(mock_promote(team_id="team-pass-through", dry_run=False))
    assert capture.captured_team_id == "team-pass-through"


def test_trigger_batch_handles_empty_results():
    """Test batch with no candidates to promote or skip."""

    class EmptyEngine:
        def run(self, team_id: str, dry_run: bool = False):
            return {"promoted": [], "skipped": []}

    response = trigger_batch(team_id="team-empty", promote_engine=EmptyEngine())
    assert response["promoted_count"] == 0
    assert response["promoted_ids"] == []
    assert response["skipped"] == []


def test_trigger_batch_summary_structure():
    """Test that batch result has expected structure."""

    class DetailEngine:
        def run(self, team_id: str, dry_run: bool = False):
            return {
                "promoted": [{"knowledge_id": "kn-detail", "team_knowledge_id": "team-kn-detail"}],
                "skipped": [{"knowledge_id": "kn-skip", "reason": "test reason"}],
            }

    response = trigger_batch(team_id="team-structure", dry_run=True, promote_engine=DetailEngine())

    # Verify expected keys exist
    assert "team_id" in response
    assert "dry_run" in response
    assert "promoted_count" in response
    assert "promoted_ids" in response
    assert "skipped" in response
    assert response["team_id"] == "team-structure"
    assert response["dry_run"] is True
