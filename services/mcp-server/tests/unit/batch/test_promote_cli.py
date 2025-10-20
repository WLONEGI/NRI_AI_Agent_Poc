from __future__ import annotations

from unittest.mock import MagicMock

import cli.promotion_cli as promotion_cli


def test_run_promotion_uses_engine(monkeypatch):
    engine = MagicMock()
    engine.run.return_value = {"promoted": [{"knowledge_id": "kn-1"}], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)

    result = promotion_cli.run_promotion("team-1", dry_run=False)

    assert result.promoted_ids == ["kn-1"]
    engine.run.assert_called_with("team-1", dry_run=False)


def test_cli_main_returns_summary(monkeypatch):
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)

    summary = promotion_cli.cli_main("team-1", dry_run=True)

    assert summary["dry_run"] is True
    engine.run.assert_called_with("team-1", dry_run=True)
