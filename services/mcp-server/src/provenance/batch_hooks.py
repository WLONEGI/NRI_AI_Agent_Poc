"""Batch promotion logging helpers."""
from __future__ import annotations

import logging

LOGGER = logging.getLogger(__name__)


def log_batch_result(*, team_id: str, promoted, skipped, dry_run: bool) -> None:
    LOGGER.info(
        "Batch promotion summary",
        extra={
            "team_id": team_id,
            "promoted": promoted,
            "skipped": skipped,
            "dry_run": dry_run,
        },
    )
