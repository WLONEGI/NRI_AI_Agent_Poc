"""Batch runner for knowledge promotion."""
from __future__ import annotations

import logging
from typing import Any, Dict

from knowledge.promotion_engine import PromotionEngine
from provenance.batch_hooks import log_batch_result

LOGGER = logging.getLogger(__name__)


def execute_batch(
    *,
    team_id: str,
    engine: PromotionEngine,
    dry_run: bool = False,
) -> Dict[str, Any]:
    result = engine.run(team_id, dry_run=dry_run)
    promoted = result["promoted"]
    skipped = result["skipped"]
    summary = {
        "promoted_count": len(promoted),
        "promoted_ids": [item["knowledge_id"] for item in promoted],
        "skipped": skipped,
        "dry_run": dry_run,
    }
    LOGGER.info("Promotion batch completed", extra={"team_id": team_id, **summary})
    log_batch_result(team_id=team_id, promoted=promoted, skipped=skipped, dry_run=dry_run)
    return summary
