"""Knowledge search service using vector and graph filters."""
from __future__ import annotations

import logging
from typing import Dict, List

from embeddings.openai_client import get_embedding_client
from knowledge.repository import KnowledgeRepository
from provenance import provenance_logger
from provenance.query_log_repository import QueryLogRepository


LOGGER = logging.getLogger(__name__)


class KnowledgeSearchService:
    def __init__(
        self,
        driver,
        repository: KnowledgeRepository | None = None,
        embedding_client=None,
        query_log_repo: QueryLogRepository | None = None,
    ):
        self._driver = driver
        self._repository = repository or KnowledgeRepository(driver)
        self._embedding_client = embedding_client or get_embedding_client()
        self._query_log_repo = query_log_repo or QueryLogRepository(driver)

    def search(self, query: str, user_id: str, *, top_k: int = 100) -> List[Dict[str, object]]:
        try:
            embedding = self._embedding_client.embed([query])[0]
        except Exception as exc:  # pragma: no cover - network failure
            LOGGER.warning("Search embedding failed", exc_info=exc)
            provenance_logger.log_search_provenance(user_id, [], query=query)
            self._query_log_repo.record_search(user_id=user_id, query=query, knowledge_ids=[])
            return []

        team_ids = self._repository.find_team_ids(user_id)
        records = self._repository.search_vector_index(
            embedding=embedding,
            user_id=user_id,
            team_ids=team_ids,
            top_k=top_k,
        )

        results: List[Dict[str, object]] = []
        for record in records:
            knowledge = record.get("knowledge", {})
            content = knowledge.get("content", "")
            summary = content[:160] + ("…" if len(content) > 160 else "") if content else ""
            owner = {
                "user_id": knowledge.get("owner_id"),
                "team_id": knowledge.get("owner_team_id"),
            }
            results.append(
                {
                    "id": knowledge.get("id"),
                    "content": content,
                    "summary": summary,
                    "similarity": record.get("similarity"),
                    "type": knowledge.get("type", "personal"),
                    "created_at": knowledge.get("created_at"),
                    "owner": owner,
                }
            )

        knowledge_ids = [item.get("id") for item in results]
        provenance_logger.log_search_provenance(user_id, knowledge_ids, query=query)
        self._query_log_repo.record_search(user_id=user_id, query=query, knowledge_ids=knowledge_ids)
        return results
