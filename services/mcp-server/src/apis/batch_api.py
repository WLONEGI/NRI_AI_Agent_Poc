"""API for triggering knowledge promotion batches."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from batch.promote import execute_batch
from infra.neo4j_client import get_driver
from knowledge.promotion_engine import PromotionEngine
from knowledge.promotion_repository import PromotionRepository

router = APIRouter()


def trigger_batch(*, team_id: str, dry_run: bool = False, promote_engine=None):
    if promote_engine is None:
        raise HTTPException(status_code=500, detail="Promotion engine not configured")
    return execute_batch(team_id=team_id, engine=promote_engine, dry_run=dry_run)


@router.post("/api/batch/promote")
async def promote(team_id: str, dry_run: bool = False):
    repository = PromotionRepository(get_driver())
    engine = PromotionEngine(repository=repository)
    return trigger_batch(team_id=team_id, dry_run=dry_run, promote_engine=engine)
