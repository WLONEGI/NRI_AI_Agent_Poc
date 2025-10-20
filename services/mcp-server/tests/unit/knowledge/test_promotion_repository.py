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


def test_fetch_personal_knowledge_handles_empty_results():
    """Test that fetch returns empty list when no candidates exist."""
    driver = MagicMock()
    driver.execute_query.return_value = []

    repo = PromotionRepository(driver=driver)
    candidates = repo.fetch_personal_knowledge(team_id="team-empty")

    assert candidates == []
    driver.execute_query.assert_called_once()


def test_fetch_personal_knowledge_handles_list_result():
    """Test that fetch handles plain list result format."""
    driver = MagicMock()
    driver.execute_query.return_value = [
        {
            "knowledge": {"id": "kn-list"},
            "similarity": 0.76,
            "contributors": ["user-a"],
            "coverage": 0.25,
        }
    ]

    repo = PromotionRepository(driver=driver)
    candidates = repo.fetch_personal_knowledge(team_id="team-list")

    assert len(candidates) == 1
    assert candidates[0]["id"] == "kn-list"
    assert candidates[0]["similarity"] == 0.76


def test_fetch_personal_knowledge_handles_multiple_candidates():
    """Test that fetch correctly processes multiple candidates."""
    driver = MagicMock()
    driver.execute_query.return_value = [
        {
            "knowledge": {"id": "kn-1"},
            "similarity": 0.85,
            "contributors": ["user-1", "user-2", "user-3"],
            "coverage": 0.60,
        },
        {
            "knowledge": {"id": "kn-2"},
            "similarity": 0.78,
            "contributors": ["user-1", "user-4"],
            "coverage": 0.40,
        },
        {
            "knowledge": {"id": "kn-3"},
            "similarity": 0.92,
            "contributors": ["user-2", "user-3", "user-4", "user-5"],
            "coverage": 0.80,
        },
    ]

    repo = PromotionRepository(driver=driver)
    candidates = repo.fetch_personal_knowledge(team_id="team-multi")

    assert len(candidates) == 3
    assert candidates[0]["id"] == "kn-1"
    assert candidates[0]["contributors"] == {"user-1", "user-2", "user-3"}
    assert candidates[1]["id"] == "kn-2"
    assert candidates[2]["similarity"] == 0.92
    assert len(candidates[2]["contributors"]) == 4


def test_promote_to_team_includes_promoted_by():
    """Test that promote passes promoted_by parameter correctly."""
    driver = MagicMock()
    driver.execute_query.return_value = [{"id": "team-kn-promoted"}]

    repo = PromotionRepository(driver=driver)
    result_id = repo.promote_to_team(
        knowledge_id="kn-promoted",
        team_id="team-test",
        promoted_by="user-admin",
    )

    assert result_id == "team-kn-promoted"
    call_args = driver.execute_query.call_args
    assert call_args.kwargs["promoted_by"] == "user-admin"


def test_promote_to_team_handles_none_promoted_by():
    """Test promotion without promoted_by parameter."""
    driver = MagicMock()
    driver.execute_query.return_value = [{"id": "team-kn-none"}]

    repo = PromotionRepository(driver=driver)
    result_id = repo.promote_to_team(knowledge_id="kn-none", team_id="team-test")

    assert result_id == "team-kn-none"
    call_args = driver.execute_query.call_args
    assert call_args.kwargs["promoted_by"] is None


def test_promote_to_team_returns_fallback_id():
    """Test that promote returns fallback ID when query returns no records."""
    driver = MagicMock()
    driver.execute_query.return_value = []

    repo = PromotionRepository(driver=driver)
    result_id = repo.promote_to_team(knowledge_id="kn-fallback", team_id="team-test")

    assert result_id == "team-kn-fallback"


def test_promote_to_team_includes_timestamp():
    """Test that promote includes promoted_at timestamp."""
    driver = MagicMock()
    driver.execute_query.return_value = [{"id": "team-kn-time"}]

    repo = PromotionRepository(driver=driver)
    repo.promote_to_team(knowledge_id="kn-time", team_id="team-test")

    call_args = driver.execute_query.call_args
    assert "promoted_at" in call_args.kwargs
    promoted_at = call_args.kwargs["promoted_at"]
    # Verify ISO format timestamp
    datetime.fromisoformat(promoted_at.replace("Z", "+00:00"))


def test_record_audit_event_includes_all_parameters():
    """Test that audit event persists all required fields."""
    driver = MagicMock()

    repo = PromotionRepository(driver=driver)
    repo.record_audit_event(
        team_id="team-audit",
        knowledge_id="kn-audit-1",
        status="promoted",
        similarity=0.82,
        contributor_count=5,
        coverage=0.71,
        reason="Exceeded all thresholds",
        dry_run=False,
    )

    driver.execute_query.assert_called_once()
    call_args = driver.execute_query.call_args
    assert call_args.kwargs["team_id"] == "team-audit"
    assert call_args.kwargs["knowledge_id"] == "kn-audit-1"
    assert call_args.kwargs["status"] == "promoted"
    assert call_args.kwargs["similarity"] == 0.82
    assert call_args.kwargs["contributor_count"] == 5
    assert call_args.kwargs["coverage"] == 0.71
    assert call_args.kwargs["reason"] == "Exceeded all thresholds"
    assert call_args.kwargs["dry_run"] is False


def test_record_audit_event_handles_dry_run():
    """Test that audit event correctly records dry_run=True."""
    driver = MagicMock()

    repo = PromotionRepository(driver=driver)
    repo.record_audit_event(
        team_id="team-dry",
        knowledge_id="kn-dry",
        status="rejected",
        similarity=0.65,
        contributor_count=2,
        coverage=0.33,
        reason="Below similarity threshold",
        dry_run=True,
    )

    call_args = driver.execute_query.call_args
    assert call_args.kwargs["dry_run"] is True
    assert call_args.kwargs["status"] == "rejected"


def test_record_audit_event_generates_audit_id():
    """Test that audit IDs follow expected pattern."""
    driver = MagicMock()

    repo = PromotionRepository(driver=driver)
    repo.record_audit_event(
        team_id="team-id",
        knowledge_id="kn-unique-123",
        status="promoted",
        similarity=0.88,
        contributor_count=4,
        coverage=0.67,
        reason="Test",
        dry_run=False,
    )

    call_args = driver.execute_query.call_args
    audit_id = call_args.kwargs["audit_id"]
    assert "kn-unique-123" in audit_id
    assert "promoted" in audit_id


def test_record_audit_event_includes_timestamp():
    """Test that audit event includes timestamp."""
    driver = MagicMock()

    repo = PromotionRepository(driver=driver)
    repo.record_audit_event(
        team_id="team-time",
        knowledge_id="kn-time",
        status="promoted",
        similarity=0.75,
        contributor_count=3,
        coverage=0.50,
        reason="Meets criteria",
        dry_run=False,
    )

    call_args = driver.execute_query.call_args
    assert "timestamp" in call_args.kwargs
    timestamp = call_args.kwargs["timestamp"]
    # Verify ISO format
    datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
