from __future__ import annotations

import logging

import pytest

from retry.backoff import run_with_backoff


def test_run_with_backoff_returns_value(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    def func() -> str:
        nonlocal calls
        calls += 1
        return "ok"

    monkeypatch.setattr("retry.backoff.time.sleep", lambda _: None)
    result = run_with_backoff(func, logger=logging.getLogger("test.backoff"), attempts=3, base_delay=0.01)

    assert result == "ok"
    assert calls == 1


def test_run_with_backoff_retries_and_logs(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    attempts = 0

    def func() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise RuntimeError("boom")
        return "ok"

    sleeps: list[float] = []
    monkeypatch.setattr("retry.backoff.time.sleep", lambda delay: sleeps.append(delay))

    with caplog.at_level(logging.WARNING):
        result = run_with_backoff(func, logger=logging.getLogger("test.backoff"), attempts=3, base_delay=0.1)

    assert result == "ok"
    assert attempts == 2
    assert sleeps == [0.1]
    warnings = [record for record in caplog.records if record.levelname == "WARNING"]
    assert any(getattr(record, "attempt", None) == 1 for record in warnings)


def test_run_with_backoff_raises_after_attempts(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    def func() -> str:
        raise ValueError("always")

    monkeypatch.setattr("retry.backoff.time.sleep", lambda _: None)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(ValueError):
            run_with_backoff(func, logger=logging.getLogger("test.backoff"), attempts=2, base_delay=0.01)

    errors = [record for record in caplog.records if record.levelname == "ERROR"]
    assert any(getattr(record, "attempts", None) == 2 for record in errors)
    assert any(getattr(record, "manual_retry_required", False) for record in errors)


def test_run_with_backoff_uses_exponential_delays(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    call_count = 0

    def func() -> str:
        nonlocal call_count
        call_count += 1
        if call_count < 4:
            raise RuntimeError("boom")
        return "ok"

    sleeps: list[float] = []
    monkeypatch.setattr("retry.backoff.time.sleep", lambda delay: sleeps.append(delay))

    with caplog.at_level(logging.WARNING):
        result = run_with_backoff(func, logger=logging.getLogger("test.backoff"), attempts=4, base_delay=1)

    assert result == "ok"
    assert sleeps == [1, 2, 4]
