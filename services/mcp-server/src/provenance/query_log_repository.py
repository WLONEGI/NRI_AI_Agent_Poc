"""Neo4j persistence for query and search provenance logs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable, Sequence
from uuid import uuid4


class QueryLogRepository:
    """Persist user query/search executions for traceability."""

    def __init__(self, driver) -> None:
        self._driver = driver

    def record_query(
        self,
        *,
        user_id: str,
        query: str,
        knowledge_id: str,
        reference_ids: Sequence[str],
        channels: Sequence[str],
        latency_ms: float,
    ) -> str:
        log_id = f"query-log-{uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        self._driver.execute_query(
            """
            MERGE (user:User {id: $user_id})
            CREATE (log:QueryLog {
                id: $log_id,
                query: $query,
                latency_ms: $latency_ms,
                channels: $channels,
                created_at: $created_at
            })
            MERGE (log)-[:INITIATED_BY]->(user)
            WITH log
            MATCH (primary:Knowledge {id: $knowledge_id})
            MERGE (log)-[:PRIMARY_RESULT]->(primary)
            WITH log
            CALL {
                WITH log
                UNWIND $reference_ids AS ref_id
                MATCH (ref:Knowledge {id: ref_id})
                MERGE (log)-[:REFERENCED]->(ref)
                RETURN count(ref_id) AS _refCount
            }
            RETURN log.id AS id
            """,
            user_id=user_id,
            log_id=log_id,
            query=query,
            knowledge_id=knowledge_id,
            reference_ids=list(reference_ids),
            channels=list(channels),
            latency_ms=latency_ms,
            created_at=created_at,
        )
        return log_id

    def record_search(
        self,
        *,
        user_id: str,
        query: str,
        knowledge_ids: Iterable[str],
    ) -> str:
        knowledge_ids = list(knowledge_ids)
        log_id = f"search-log-{uuid4()}"
        created_at = datetime.now(timezone.utc).isoformat()
        self._driver.execute_query(
            """
            MERGE (user:User {id: $user_id})
            CREATE (log:SearchLog {
                id: $log_id,
                query: $query,
                result_count: $result_count,
                created_at: $created_at
            })
            MERGE (log)-[:INITIATED_BY]->(user)
            WITH log
            CALL {
                WITH log
                UNWIND $knowledge_ids AS kid
                MATCH (k:Knowledge {id: kid})
                MERGE (log)-[:RETURNED]->(k)
                RETURN count(kid) AS _count
            }
            RETURN log.id AS id
            """,
            user_id=user_id,
            log_id=log_id,
            query=query,
            knowledge_ids=knowledge_ids,
            result_count=len(knowledge_ids),
            created_at=created_at,
        )
        return log_id
