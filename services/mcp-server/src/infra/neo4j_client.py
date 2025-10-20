"""Neo4j driver factory and health checks."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

try:  # pragma: no cover - optional dependency for unit tests
    from neo4j import GraphDatabase, Driver  # type: ignore
except ImportError:  # pragma: no cover - fallback shim
    GraphDatabase = None  # type: ignore
    Driver = object  # type: ignore

from config.settings import get_settings

_driver: Optional[Driver] = None


def get_driver() -> Driver:
    """Return a singleton Neo4j driver instance."""

    global _driver
    if _driver is None:
        if GraphDatabase is None:  # pragma: no cover - optional dependency not installed
            raise RuntimeError("Neo4j Python driver is not installed. Install 'neo4j' package to continue.")
        settings = get_settings()
        _driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
    return _driver


@contextmanager
def get_session(**kwargs) -> Iterator:
    """Yield a Neo4j session using the shared driver."""

    driver = get_driver()
    session = driver.session(**kwargs)
    try:
        yield session
    finally:
        session.close()


def health_check() -> bool:
    """Run a lightweight query to confirm connectivity."""

    with get_session() as session:
        result = session.run("RETURN 1 AS ok")
        record = result.single()
        return bool(record and record.get("ok") == 1)


def close_driver() -> None:
    """Close the cached driver if it exists."""

    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
