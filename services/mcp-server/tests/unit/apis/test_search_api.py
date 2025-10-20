from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from fastapi import HTTPException

from apis.search_api import SearchResponse, search_endpoint


def test_search_endpoint_returns_results() -> None:
    service = MagicMock()
    service.search.return_value = [
        {
            "id": "kn-1",
            "summary": "summary",
            "similarity": 0.9,
            "type": "personal",
            "created_at": "2025-10-19T00:00:00Z",
            "owner": {"user_id": "user-1"},
        }
    ]
    response = search_endpoint(query="match", user_id="user-1", top_k=10, service=service)
    assert isinstance(response, SearchResponse)
    assert response.top_k == 10
    assert response.results[0].id == "kn-1"
    service.search.assert_called_with("match", "user-1", top_k=10)


def test_search_endpoint_rejects_blank_query() -> None:
    with pytest.raises(HTTPException) as exc_info:
        search_endpoint(query=" ", user_id="user-1")
    assert exc_info.value.status_code == 400
