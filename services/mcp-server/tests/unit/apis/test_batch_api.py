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
