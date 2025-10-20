"""Query personal + team knowledge from Neo4j."""
from __future__ import annotations

import logging
from typing import Dict, List, Sequence

from embeddings.openai_client import get_embedding_client
from infra.neo4j_client import get_driver


LOGGER = logging.getLogger(__name__)


def _unwrap(result) -> Sequence[Dict[str, object]]:
    if isinstance(result, tuple):  # neo4j execute_query may return (records, summary, keys)
        return result[0]
    return result


def query_team_knowledge(
    *,
    query: str,
    user_id: str,
    driver=None,
    embedding_client=None,
    top_k: int = 100,
) -> List[Dict[str, object]]:
    driver = driver or get_driver()
    embedding_client = embedding_client or get_embedding_client()

    try:
        embedding_vector = embedding_client.embed([query])[0]
    except Exception as exc:  # pragma: no cover - network or SDK failure
        LOGGER.warning("Embedding generation failed for query_team_knowledge", exc_info=exc)
        return []

    team_result = driver.execute_query(
        """
        MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(t:Team)
        RETURN collect(t.id) AS team_ids
        """,
        user_id=user_id,
    )
    records = _unwrap(team_result)
    team_ids: List[str] = []
    if records:
        first = records[0]
        if isinstance(first, dict):
            team_ids = [tid for tid in (first.get("team_ids") or []) if isinstance(tid, str)]

    search_result = driver.execute_query(
        """
        CALL db.index.vector.queryNodes('knowledge_embedding', $top_k, $embedding)
        YIELD node, score
        WHERE (
            coalesce(node.type, 'personal') = 'personal' AND node.owner_id = $user_id
        ) OR (
            coalesce(node.type, 'personal') = 'team' AND node.owner_team_id IN $team_ids
        )
        RETURN node AS knowledge, score AS similarity
        ORDER BY similarity DESC
        LIMIT $top_k
        """,
        user_id=user_id,
        team_ids=team_ids,
        embedding=embedding_vector,
        top_k=top_k,
    )

    return [
        {
            "id": record["knowledge"]["id"],
            "content": record["knowledge"].get("content"),
            "similarity": record.get("similarity", 0.0),
            "type": record["knowledge"].get("type"),
            "owner_id": record["knowledge"].get("owner_id"),
            "owner_team_id": record["knowledge"].get("owner_team_id"),
        }
        for record in _unwrap(search_result)
    ]
