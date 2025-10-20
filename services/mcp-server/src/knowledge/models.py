"""Knowledge domain models and mappers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


type Embedding = List[float]


@dataclass
class KnowledgeRecord:
    knowledge_id: str
    knowledge_type: str  # personal or team
    content: str
    category: Optional[str]
    hierarchy_level: int
    owner_id: Optional[str]
    team_id: Optional[str]
    confidence: float
    embedding: Optional[Embedding]
    created_at: str
    tags: List[str]


@dataclass
class Provenance:
    query_id: str
    agent_execution_id: str
    tool_execution_id: str
    data_source_id: str
    extracted_content_id: str


@dataclass
class KnowledgeWithProvenance:
    record: KnowledgeRecord
    provenance: Provenance


def record_from_node(node: Dict[str, Any]) -> KnowledgeRecord:
    return KnowledgeRecord(
        knowledge_id=node["id"],
        knowledge_type=node.get("type", "personal"),
        content=node.get("content", ""),
        category=node.get("category"),
        hierarchy_level=node.get("hierarchy_level", 1),
        owner_id=node.get("owner_id"),
        team_id=node.get("team_id"),
        confidence=node.get("confidence", 0.0),
        embedding=node.get("embedding"),
        created_at=node.get("created_at", ""),
        tags=node.get("tags", []),
    )
