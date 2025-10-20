"""Provenance logging helpers."""
from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)


def log_search_provenance(user_id: str, knowledge_ids, query: str | None = None) -> None:
    LOGGER.info(
        "search_executed",
        extra={
            "user_id": user_id,
            "knowledge_ids": knowledge_ids,
            "query": query,
        },
    )


def log_query_success(*, user_id: str, knowledge_id: str, latency_ms: float, channels: list[str]) -> None:
    LOGGER.info(
        "query_success",
        extra={
            "user_id": user_id,
            "knowledge_id": knowledge_id,
            "latency_ms": latency_ms,
            "channels": channels,
        },
    )


def log_query_failure(*, user_id: str, query: str, reason: str) -> None:
    LOGGER.error(
        "query_failure",
        extra={"user_id": user_id, "query": query, "reason": reason},
    )
