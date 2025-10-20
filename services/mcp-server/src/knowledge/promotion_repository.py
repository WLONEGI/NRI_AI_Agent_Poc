"""Data access layer for promotion workflows."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Sequence


FETCH_CANDIDATES_QUERY = """
MATCH (team:Team {id: $team_id})
MATCH (source:Knowledge {type: 'personal'})-[:ATTRIBUTED_TO]->(owner:User)
WHERE (source)-[:BELONGS_TO]->(team)
  AND (owner)-[:MEMBER_OF]->(team)
OPTIONAL MATCH (source)<-[:CONTRIBUTED_TO]-(contributor:User)
WITH team, source, collect(DISTINCT contributor.id) AS contributors,
     size((team)<-[:MEMBER_OF]-(:User)) AS team_size
RETURN source AS knowledge,
       coalesce(source.promotion_similarity, source.confidence, 0.0) AS similarity,
       contributors AS contributors,
       CASE WHEN team_size = 0 THEN 0 ELSE size(contributors) * 1.0 / team_size END AS coverage
"""


PROMOTE_TO_TEAM_QUERY = """
MATCH (source:Knowledge {id: $knowledge_id})
MATCH (team:Team {id: $team_id})
CREATE (team_knowledge:Knowledge {
    id: $team_knowledge_id,
    type: 'team',
    content: source.content,
    category: source.category,
    hierarchy_level: 2,
    owner_team_id: $team_id,
    team_id: $team_id,
    confidence: source.confidence,
    created_at: $promoted_at,
    tags: source.tags
})
SET team_knowledge.vector_created_at = coalesce(source.vector_created_at, $promoted_at)
MERGE (source)-[:PROMOTED_TO]->(team_knowledge)
MERGE (team_knowledge)-[:BELONGS_TO]->(team)
RETURN team_knowledge.id AS id
"""


AUDIT_QUERY = """
MATCH (team:Team {id: $team_id})
CREATE (audit:PromotionAudit {
    id: $audit_id,
    status: $status,
    similarity: $similarity,
    contributor_count: $contributor_count,
    coverage: $coverage,
    dry_run: $dry_run,
    reason: $reason,
    created_at: $timestamp
})
SET audit.knowledge_id = $knowledge_id
MERGE (audit)-[:FOR_TEAM]->(team)
RETURN audit.id AS id
"""


@dataclass
class PromotionCandidate:
    id: str
    similarity: float
    contributors: Iterable[str]
    coverage: float


class PromotionRepository:
    """Provides database operations required by the promotion engine."""

    def __init__(self, driver) -> None:
        self._driver = driver

    def fetch_personal_knowledge(self, team_id: str) -> List[Dict[str, Any]]:
        result = self._driver.execute_query(FETCH_CANDIDATES_QUERY, team_id=team_id)
        records = _unwrap_records(result)
        candidates: List[Dict[str, Any]] = []
        for record in records:
            knowledge = record.get("knowledge", {})
            candidates.append(
                {
                    "id": knowledge.get("id"),
                    "similarity": record.get("similarity", 0.0),
                    "contributors": set(record.get("contributors", [])),
                    "coverage": record.get("coverage", 0.0),
                }
            )
        return candidates

    def promote_to_team(self, *, knowledge_id: str, team_id: str, promoted_by: str | None = None) -> str:
        team_knowledge_id = f"team-{knowledge_id}"
        promoted_at = datetime.now(timezone.utc).isoformat()
        result = self._driver.execute_query(
            PROMOTE_TO_TEAM_QUERY,
            knowledge_id=knowledge_id,
            team_id=team_id,
            team_knowledge_id=team_knowledge_id,
            promoted_at=promoted_at,
            promoted_by=promoted_by,
        )
        records = _unwrap_records(result)
        return records[0]["id"] if records else team_knowledge_id

    def record_audit_event(
        self,
        *,
        team_id: str,
        knowledge_id: str,
        status: str,
        similarity: float,
        contributor_count: int,
        coverage: float,
        reason: str,
        dry_run: bool,
    ) -> None:
        self._driver.execute_query(
            AUDIT_QUERY,
            team_id=team_id,
            knowledge_id=knowledge_id,
            status=status,
            similarity=similarity,
            contributor_count=contributor_count,
            coverage=coverage,
            dry_run=dry_run,
            reason=reason,
            audit_id=f"audit-{knowledge_id}-{status}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


def _unwrap_records(result: Sequence[Any]) -> List[Dict[str, Any]]:
    if isinstance(result, tuple):  # neo4j driver: (records, summary, keys)
        return list(result[0] or [])
    return list(result or [])
