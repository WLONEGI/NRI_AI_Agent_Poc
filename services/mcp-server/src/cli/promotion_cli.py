"""Reusable entrypoint for promotion CLI and tooling."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from infra.neo4j_client import close_driver, get_driver
from knowledge.promotion_engine import PromotionEngine
from knowledge.promotion_repository import PromotionRepository

LOGGER = logging.getLogger(__name__)


@dataclass
class PromotionResult:
    promoted_ids: list[str]
    skipped: list[dict]


def build_engine() -> PromotionEngine:
    repository = PromotionRepository(get_driver())
    return PromotionEngine(repository=repository, logger=LOGGER)


def run_promotion(team_id: str, *, dry_run: bool = False) -> PromotionResult:
    engine = build_engine()
    result = engine.run(team_id, dry_run=dry_run)
    close_driver()
    return PromotionResult(
        promoted_ids=[item["knowledge_id"] for item in result["promoted"]],
        skipped=result["skipped"],
    )


def cli_main(team_id: str, *, dry_run: bool = False) -> dict:
    engine = build_engine()
    summary = {
        "team_id": team_id,
        **engine.run(team_id, dry_run=dry_run),
        "dry_run": dry_run,
    }
    close_driver()
    return summary

