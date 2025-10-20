"""Application settings management using environment variables."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


class AppSettings:
    """Centralised application configuration without third-party dependencies."""

    def __init__(self) -> None:
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "test-key")
        self.neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD", "test")
        self.mcp_server_url = os.getenv("MCP_SERVER_URL", "http://localhost:3000")
        self.log_dir = Path(os.getenv("LOG_DIR", "logs"))


_settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Return a cached settings instance."""

    global _settings
    if _settings is None:
        _settings = AppSettings()
    return _settings
