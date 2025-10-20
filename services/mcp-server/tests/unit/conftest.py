"""Pytest fixtures for MCP server unit tests."""
from __future__ import annotations

from pathlib import Path
from typing import Iterator

import pytest

from config.settings import AppSettings, get_settings


@pytest.fixture(scope="session")
def settings(tmp_path_factory: pytest.TempPathFactory) -> AppSettings:
    """Provide test settings with isolated log directory."""

    log_dir = tmp_path_factory.mktemp("logs")

    # Create AppSettings instance and override with test values
    test_settings = AppSettings()
    test_settings.openai_api_key = "test-key"
    test_settings.neo4j_uri = "bolt://localhost:7687"
    test_settings.neo4j_user = "neo4j"
    test_settings.neo4j_password = "test"
    test_settings.mcp_server_url = "http://localhost:3000"
    test_settings.log_dir = Path(log_dir)

    return test_settings


@pytest.fixture(autouse=True)
def _override_settings(monkeypatch: pytest.MonkeyPatch, settings: AppSettings) -> Iterator[None]:
    """Ensure tests use the fixture settings and reset after run."""

    original_settings = get_settings()
    monkeypatch.setattr("config.settings._settings", settings)
    yield
    # reset global settings cache
    monkeypatch.setattr("config.settings._settings", original_settings)
