"""API endpoint for executing agent queries and persisting knowledge."""
from __future__ import annotations

import logging
import time
import uuid
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from agents.langgraph_runner import run_agent
from infra.neo4j_client import get_driver
from knowledge.repository import KnowledgeRepository
from provenance.provenance_logger import log_query_failure, log_query_success
from provenance.query_log_repository import QueryLogRepository
from tools.save_knowledge import save_knowledge


router = APIRouter()
LOGGER = logging.getLogger(__name__)


class Attachment(BaseModel):
    path: str
    mime_type: str
    checksum: Optional[str] = None


class QueryRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    query: str = Field(..., min_length=1)
    channels: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, str]] = None
    attachments: List[Attachment] = Field(default_factory=list)


class OwnerInfo(BaseModel):
    user_id: Optional[str] = None
    team_id: Optional[str] = None


class ProvenanceItem(BaseModel):
    id: str
    source_type: str
    summary: Optional[str] = None
    similarity: Optional[float] = None
    owner: Optional[OwnerInfo] = None
    created_at: Optional[str] = None


class ToolTrace(BaseModel):
    name: str
    input: Dict[str, object]
    output: Dict[str, object]


class QueryResponse(BaseModel):
    answer: str
    knowledge_id: str
    knowledge_level: str
    provenance: List[ProvenanceItem]
    references: List[ProvenanceItem]
    retries: int = 0
    logs_written: bool = True
    latency_ms: float
    tool_traces: Optional[List[ToolTrace]] = None


def _serialise_provenance(items: List[Dict[str, object]]) -> List[ProvenanceItem]:
    return [
        ProvenanceItem(
            id=item.get("id") or str(uuid.uuid4()),
            source_type=item.get("source_type", "unknown"),
            summary=item.get("summary"),
            similarity=item.get("similarity"),
            owner=OwnerInfo(**item.get("owner", {})) if item.get("owner") else None,
            created_at=item.get("created_at"),
        )
        for item in items
    ]


def handle_query(
    request: QueryRequest,
    *,
    repo: KnowledgeRepository | None = None,
    agent_runner=run_agent,
    logger: logging.Logger = LOGGER,
    query_log_repo: QueryLogRepository | None = None,
) -> QueryResponse:
    driver = get_driver()
    repo = repo or KnowledgeRepository(driver)
    query_log_repo = query_log_repo or QueryLogRepository(driver)

    start = time.perf_counter()
    try:
        agent_result = agent_runner(
            query=request.query,
            user_id=request.user_id,
            channels=request.channels,
            metadata=request.metadata or {},
            attachments=[attachment.dict() for attachment in request.attachments],
        )
    except Exception as exc:  # pragma: no cover - defensive
        log_query_failure(user_id=request.user_id, query=request.query, reason="agent_execution_failed")
        logger.exception("Agent execution failed")
        raise HTTPException(status_code=500, detail="Agent execution failed") from exc

    knowledge_payload = {
        "knowledge": agent_result["knowledge"],
        "provenance": agent_result["provenance"],
    }

    try:
        knowledge_id = save_knowledge(knowledge_payload, repo=repo, logger=logger)
    except Exception as exc:  # pragma: no cover - defensive
        log_query_failure(user_id=request.user_id, query=request.query, reason="persistence_failed")
        logger.exception("Knowledge persistence failed")
        raise HTTPException(status_code=500, detail="Knowledge persistence failed") from exc

    latency_ms = (time.perf_counter() - start) * 1000
    log_query_success(
        user_id=request.user_id,
        knowledge_id=knowledge_id,
        latency_ms=latency_ms,
        channels=request.channels,
    )

    reference_ids = [
        ref.get("id")
        for ref in agent_result.get("references", [])
        if isinstance(ref, dict) and ref.get("id")
    ]
    try:
        query_log_repo.record_query(
            user_id=request.user_id,
            query=request.query,
            knowledge_id=knowledge_id,
            reference_ids=reference_ids,
            channels=request.channels,
            latency_ms=latency_ms,
        )
    except Exception as exc:  # pragma: no cover - logging failures tolerated
        logger.warning("Failed to persist query log", exc_info=exc)

    response = QueryResponse(
        answer=agent_result.get("answer", ""),
        knowledge_id=knowledge_id,
        knowledge_level=agent_result["knowledge"].get("type", "personal"),
        provenance=_serialise_provenance(agent_result.get("provenance_chain", [])),
        references=_serialise_provenance(agent_result.get("references", [])),
        retries=agent_result.get("retries", 0),
        logs_written=True,
        latency_ms=latency_ms,
        tool_traces=[ToolTrace(**trace) for trace in agent_result.get("tool_traces", [])] or None,
    )
    return response


@router.post("/api/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest) -> QueryResponse:
    return handle_query(request)
