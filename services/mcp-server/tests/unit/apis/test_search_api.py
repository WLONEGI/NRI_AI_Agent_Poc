from __future__ import annotations

from unittest.mock import MagicMock

from apis.search_api import search_endpoint


def test_search_endpoint_returns_results():
    service = MagicMock()
    service.search.return_value = [{"id": "kn", "content": "match"}]
    response = search_endpoint(query="match", user_id="user-1", service=service)
    assert response == {"results": [{"id": "kn", "content": "match"}]}
