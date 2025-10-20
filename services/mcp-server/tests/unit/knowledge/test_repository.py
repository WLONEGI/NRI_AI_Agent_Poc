from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from knowledge.models import KnowledgeRecord, Provenance
from knowledge.repository import KnowledgeRepository


@pytest.fixture
def sample_record() -> KnowledgeRecord:
    return KnowledgeRecord(
        knowledge_id="kn-1",
        knowledge_type="personal",
        content="sample",
        category="general",
        hierarchy_level=1,
        owner_id="user-1",
        team_id=None,
        confidence=0.8,
        embedding=[0.1, 0.2, 0.3],
        created_at="2025-10-17T00:00:00Z",
        tags=["demo"],
    )


@pytest.fixture
def sample_provenance() -> Provenance:
    return Provenance(
        query_id="q-1",
        agent_execution_id="ae-1",
        tool_execution_id="te-1",
        data_source_id="ds-1",
        extracted_content_id="ec-1",
    )


def test_save_knowledge_persists_full_provenance(sample_record: KnowledgeRecord, sample_provenance: Provenance) -> None:
    driver = MagicMock()
    repo = KnowledgeRepository(driver)

    repo.save(sample_record, sample_provenance)

    assert driver.execute_query.called, "Expected execute_query to be invoked"
    query, params = driver.execute_query.call_args[0][0], driver.execute_query.call_args[1]
    assert "MERGE (q:Query" in query
    assert "ATTRIBUTED_TO" in query
    assert "BELONGS_TO" in query
    assert params["knowledge"]["id"] == "kn-1"
    assert params["knowledge"].get("owner_team_id") is None
    assert params["provenance"]["query_id"] == "q-1"


def test_save_knowledge_handles_missing_embedding(sample_provenance: Provenance) -> None:
    driver = MagicMock()
    repo = KnowledgeRepository(driver)
    record = KnowledgeRecord(
        knowledge_id="kn-2",
        knowledge_type="team",
        content="team content",
        category=None,
        hierarchy_level=2,
        owner_id=None,
        team_id="team-1",
        confidence=0.5,
        embedding=None,
        created_at="2025-10-17T00:00:00Z",
        tags=[],
    )

    repo.save(record, sample_provenance)

    query, params = driver.execute_query.call_args[0][0], driver.execute_query.call_args[1]
    assert params["knowledge"]["embedding"] is None
    assert params["knowledge"]["owner_team_id"] == "team-1"
    assert "BELONGS_TO" in query
