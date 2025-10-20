"""API endpoint for knowledge search."""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from infra.neo4j_client import get_driver
from knowledge.search_service import KnowledgeSearchService


router = APIRouter()
LOGGER = logging.getLogger(__name__)


class SearchResult(BaseModel):
    id: str
    summary: Optional[str]
    similarity: Optional[float]
    type: Optional[str]
    created_at: Optional[str]
    owner: Optional[dict]


class SearchResponse(BaseModel):
    query: str
    user_id: str
    top_k: int
    results: List[SearchResult]


def search_endpoint(*, query: str, user_id: str, top_k: int = 100, service=None) -> SearchResponse:
    if not query.strip():
        raise HTTPException(status_code=400, detail="Query must not be empty")
    if not user_id.strip():
        raise HTTPException(status_code=400, detail="user_id must not be empty")

    service = service or KnowledgeSearchService(get_driver())

    try:
        results = service.search(query, user_id, top_k=top_k)
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Search failed")
        raise HTTPException(status_code=500, detail="Knowledge search failed") from exc

    return SearchResponse(
        query=query,
        user_id=user_id,
        top_k=top_k,
        results=[SearchResult(**item) for item in results],
    )


@router.get("/api/knowledge/search", response_model=SearchResponse)
async def search(
    query: str = Query(..., min_length=1),
    user_id: str = Query(..., min_length=1),
    top_k: int = Query(100, ge=1, le=100),
):
    return search_endpoint(query=query, user_id=user_id, top_k=top_k)

