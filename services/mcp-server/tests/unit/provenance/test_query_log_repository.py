from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from provenance.query_log_repository import QueryLogRepository


def _freeze_time(monkeypatch, iso: str) -> None:
    fake_datetime = SimpleNamespace(now=lambda tz=None: SimpleNamespace(isoformat=lambda: iso))
    monkeypatch.setattr("provenance.query_log_repository.datetime", fake_datetime)


def _freeze_uuid(monkeypatch, values):
    iterator = iter(values)
    monkeypatch.setattr("provenance.query_log_repository.uuid4", lambda: next(iterator))


def test_record_query_persists_log(monkeypatch) -> None:
    driver = MagicMock()
    repo = QueryLogRepository(driver)

    _freeze_time(monkeypatch, "2025-10-19T00:00:00Z")
    _freeze_uuid(monkeypatch, ["abc"])

    log_id = repo.record_query(
        user_id="user-1",
        query="hello",
        knowledge_id="kn-1",
        reference_ids=["kn-2"],
        channels=["file_search"],
        latency_ms=123.4,
    )

    assert log_id == "query-log-abc"
    assert driver.execute_query.called
    _, kwargs = driver.execute_query.call_args
    assert kwargs["user_id"] == "user-1"
    assert kwargs["reference_ids"] == ["kn-2"]
    assert kwargs["channels"] == ["file_search"]
    assert kwargs["created_at"] == "2025-10-19T00:00:00Z"


def test_record_search_persists_log(monkeypatch) -> None:
    driver = MagicMock()
    repo = QueryLogRepository(driver)

    _freeze_time(monkeypatch, "2025-10-19T01:00:00Z")
    _freeze_uuid(monkeypatch, ["def"])

    log_id = repo.record_search(user_id="user-1", query="keyword", knowledge_ids=["kn-1", "kn-2"])

    assert log_id == "search-log-def"
    assert driver.execute_query.called
    _, kwargs = driver.execute_query.call_args
    assert kwargs["knowledge_ids"] == ["kn-1", "kn-2"]
    assert kwargs["result_count"] == 2
    assert kwargs["created_at"] == "2025-10-19T01:00:00Z"
