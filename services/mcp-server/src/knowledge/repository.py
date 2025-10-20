"""Persistence layer for knowledge records and provenance."""
from __future__ import annotations

from typing import Any, Dict, List

from .models import KnowledgeRecord, Provenance


class KnowledgeRepository:
    def __init__(self, driver) -> None:
        self._driver = driver

    def save(self, record: KnowledgeRecord, provenance: Provenance) -> str:
        knowledge = {
            "id": record.knowledge_id,
            "type": record.knowledge_type,
            "content": record.content,
            "category": record.category,
            "hierarchy_level": record.hierarchy_level,
            "owner_id": record.owner_id,
            "team_id": record.team_id,
            "confidence": record.confidence,
            "embedding": record.embedding,
            "created_at": record.created_at,
            "tags": record.tags,
        }
        if record.team_id:
            knowledge["owner_team_id"] = record.team_id

        params = {
            "knowledge": knowledge,
            "provenance": {
                "query_id": provenance.query_id,
                "agent_execution_id": provenance.agent_execution_id,
                "tool_execution_id": provenance.tool_execution_id,
                "data_source_id": provenance.data_source_id,
                "extracted_content_id": provenance.extracted_content_id,
            },
        }

        query = """
        MERGE (k:Knowledge {id: $knowledge.id})
        SET k += $knowledge
        WITH k, $knowledge AS knowledge, $provenance AS provenance
        CALL {
            WITH k, knowledge
            WHERE knowledge.owner_id IS NOT NULL
            MERGE (owner:User {id: knowledge.owner_id})
            MERGE (k)-[:ATTRIBUTED_TO]->(owner)
            RETURN NULL
        }
        CALL {
            WITH k, knowledge
            WHERE knowledge.team_id IS NOT NULL
            MERGE (team:Team {id: knowledge.team_id})
            MERGE (k)-[:BELONGS_TO]->(team)
            RETURN NULL
        }
        CALL {
            WITH knowledge
            WHERE knowledge.owner_id IS NOT NULL AND knowledge.team_id IS NOT NULL
            MERGE (owner:User {id: knowledge.owner_id})
            MERGE (team:Team {id: knowledge.team_id})
            MERGE (owner)-[:MEMBER_OF]->(team)
            RETURN NULL
        }
        WITH k, knowledge, provenance
        MERGE (q:Query {id: provenance.query_id})
        MERGE (ae:AgentExecution {id: provenance.agent_execution_id})
        MERGE (te:ToolExecution {id: provenance.tool_execution_id})
        MERGE (ds:DataSource {id: provenance.data_source_id})
        MERGE (ec:ExtractedContent {id: provenance.extracted_content_id})
        MERGE (q)-[:TRIGGERED]->(ae)
        MERGE (ae)-[:USED]->(te)
        MERGE (te)-[:GENERATED]->(ds)
        MERGE (ec)-[:DERIVED_FROM]->(ds)
        MERGE (k)-[:SYNTHESIZED_FROM]->(ec)
        RETURN k.id AS id
        """

        result = self._driver.execute_query(query, knowledge=params["knowledge"], provenance=params["provenance"])
        if isinstance(result, tuple):  # handle neo4j.execute_query returning (records, summary, keys)
            records = result[0]
        else:
            records = result
        return records[0]["id"] if records else record.knowledge_id

    def find_team_ids(self, user_id: str) -> List[str]:
        result = self._driver.execute_query(
            """
            MATCH (u:User {id: $user_id})-[:MEMBER_OF]->(t:Team)
            RETURN collect(t.id) AS team_ids
            """,
            user_id=user_id,
        )
        records = result[0] if isinstance(result, tuple) else result
        if not records:
            return []
        team_ids = records[0].get("team_ids", [])
        return [tid for tid in team_ids if isinstance(tid, str)]

    def search_vector_index(
        self,
        *,
        embedding: List[float],
        user_id: str,
        team_ids: List[str],
        top_k: int = 100,
    ) -> List[Dict[str, Any]]:
        result = self._driver.execute_query(
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
            embedding=embedding,
            user_id=user_id,
            team_ids=team_ids,
            top_k=top_k,
        )
        records = result[0] if isinstance(result, tuple) else result
        return list(records)
