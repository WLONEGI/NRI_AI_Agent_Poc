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


def test_run_promotion_closes_driver(monkeypatch):
    """Test that run_promotion closes the driver after execution."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)

    close_calls = []
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: close_calls.append(1))

    promotion_cli.run_promotion("team-close", dry_run=False)

    assert len(close_calls) == 1


def test_cli_main_closes_driver(monkeypatch):
    """Test that cli_main closes the driver after execution."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)

    close_calls = []
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: close_calls.append(1))

    promotion_cli.cli_main("team-close", dry_run=True)

    assert len(close_calls) == 1


def test_run_promotion_handles_multiple_promotions(monkeypatch):
    """Test run_promotion with multiple successful promotions."""
    engine = MagicMock()
    engine.run.return_value = {
        "promoted": [
            {"knowledge_id": "kn-1"},
            {"knowledge_id": "kn-2"},
            {"knowledge_id": "kn-3"},
        ],
        "skipped": [],
    }
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    result = promotion_cli.run_promotion("team-multi", dry_run=False)

    assert len(result.promoted_ids) == 3
    assert "kn-1" in result.promoted_ids
    assert "kn-2" in result.promoted_ids
    assert "kn-3" in result.promoted_ids
    assert result.skipped == []


def test_run_promotion_handles_all_skipped(monkeypatch):
    """Test run_promotion when all candidates are skipped."""
    engine = MagicMock()
    engine.run.return_value = {
        "promoted": [],
        "skipped": [
            {"knowledge_id": "kn-skip-1", "reason": "Low similarity"},
            {"knowledge_id": "kn-skip-2", "reason": "Low coverage"},
        ],
    }
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    result = promotion_cli.run_promotion("team-skip", dry_run=False)

    assert result.promoted_ids == []
    assert len(result.skipped) == 2
    assert result.skipped[0]["reason"] == "Low similarity"


def test_run_promotion_handles_mixed_results(monkeypatch):
    """Test run_promotion with both promoted and skipped candidates."""
    engine = MagicMock()
    engine.run.return_value = {
        "promoted": [{"knowledge_id": "kn-promoted"}],
        "skipped": [{"knowledge_id": "kn-skipped", "reason": "Below threshold"}],
    }
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    result = promotion_cli.run_promotion("team-mixed", dry_run=False)

    assert result.promoted_ids == ["kn-promoted"]
    assert len(result.skipped) == 1
    assert result.skipped[0]["knowledge_id"] == "kn-skipped"


def test_run_promotion_respects_dry_run_flag(monkeypatch):
    """Test that dry_run flag is passed to engine in run_promotion."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    promotion_cli.run_promotion("team-dry", dry_run=True)

    engine.run.assert_called_with("team-dry", dry_run=True)


def test_cli_main_includes_team_id_in_summary(monkeypatch):
    """Test that cli_main includes team_id in the result."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    summary = promotion_cli.cli_main("team-verify", dry_run=False)

    assert summary["team_id"] == "team-verify"


def test_cli_main_includes_engine_results(monkeypatch):
    """Test that cli_main includes promoted and skipped from engine."""
    engine = MagicMock()
    engine.run.return_value = {
        "promoted": [{"knowledge_id": "kn-engine"}],
        "skipped": [{"knowledge_id": "kn-skip", "reason": "test"}],
    }
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    summary = promotion_cli.cli_main("team-result", dry_run=False)

    assert "promoted" in summary
    assert "skipped" in summary
    assert len(summary["promoted"]) == 1
    assert summary["promoted"][0]["knowledge_id"] == "kn-engine"


def test_cli_main_respects_dry_run_flag(monkeypatch):
    """Test that cli_main passes dry_run to engine and includes it in result."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    summary = promotion_cli.cli_main("team-flag", dry_run=True)

    engine.run.assert_called_with("team-flag", dry_run=True)
    assert summary["dry_run"] is True


def test_cli_main_defaults_dry_run_false(monkeypatch):
    """Test that cli_main defaults dry_run to False."""
    engine = MagicMock()
    engine.run.return_value = {"promoted": [], "skipped": []}
    monkeypatch.setattr(promotion_cli, "build_engine", lambda: engine)
    monkeypatch.setattr(promotion_cli, "close_driver", lambda: None)

    summary = promotion_cli.cli_main("team-default")

    engine.run.assert_called_with("team-default", dry_run=False)
    assert summary["dry_run"] is False


def test_build_engine_creates_promotion_engine(monkeypatch):
    """Test that build_engine creates PromotionEngine with repository."""
    mock_driver = MagicMock()
    mock_repo = MagicMock()
    mock_engine = MagicMock()

    monkeypatch.setattr(promotion_cli, "get_driver", lambda: mock_driver)
    monkeypatch.setattr(promotion_cli, "PromotionRepository", lambda driver: mock_repo)
    monkeypatch.setattr(promotion_cli, "PromotionEngine", lambda repository, logger=None: mock_engine)

    engine = promotion_cli.build_engine()

    assert engine == mock_engine


def test_promotion_result_dataclass_structure():
    """Test that PromotionResult has expected structure."""
    from cli.promotion_cli import PromotionResult

    result = PromotionResult(
        promoted_ids=["kn-1", "kn-2"],
        skipped=[{"knowledge_id": "kn-skip", "reason": "test"}],
    )

    assert result.promoted_ids == ["kn-1", "kn-2"]
    assert len(result.skipped) == 1
    assert result.skipped[0]["knowledge_id"] == "kn-skip"
