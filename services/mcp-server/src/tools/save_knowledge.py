"""save_knowledge MCP tool implementation."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from embeddings.openai_client import get_embedding_client
from knowledge.models import KnowledgeRecord, Provenance
from knowledge.repository import KnowledgeRepository
from config.settings import get_settings
from infra.neo4j_client import get_driver


def save_knowledge(
    payload: Dict[str, Any],
    *,
    repo: Optional[KnowledgeRepository] = None,
    embedding_client=None,
    logger: Optional[logging.Logger] = None,
) -> str:
    """Persist knowledge content and provenance."""

    repo = repo or KnowledgeRepository(get_driver())
    embedding_client = embedding_client or get_embedding_client()
    logger = logger or logging.getLogger(__name__)

    knowledge_data = payload["knowledge"]
    provenance_data = payload["provenance"]

    embedding = None
    try:
        embedding = embedding_client.embed([knowledge_data["content"]])[0]
    except Exception as exc:  # pragma: no cover - network failure in production
        logger.warning("Embedding generation failed", exc_info=exc)

    record = KnowledgeRecord(
        knowledge_id=knowledge_data["id"],
        knowledge_type=knowledge_data.get("type", "personal"),
        content=knowledge_data["content"],
        category=knowledge_data.get("category"),
        hierarchy_level=knowledge_data.get("hierarchy_level", 1),
        owner_id=knowledge_data.get("owner_id"),
        team_id=knowledge_data.get("team_id"),
        confidence=knowledge_data.get("confidence", 0.0),
        embedding=embedding,
        created_at=knowledge_data.get("created_at", ""),
        tags=knowledge_data.get("tags", []),
    )

    provenance = Provenance(
        query_id=provenance_data["query_id"],
        agent_execution_id=provenance_data["agent_execution_id"],
        tool_execution_id=provenance_data["tool_execution_id"],
        data_source_id=provenance_data["data_source_id"],
        extracted_content_id=provenance_data["extracted_content_id"],
    )

    knowledge_id = repo.save(record, provenance)
    return knowledge_id
