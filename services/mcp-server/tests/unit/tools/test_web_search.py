from __future__ import annotations

from tools.web_search import web_search


def test_web_search_parses_response() -> None:
    def fake_fetch(url: str) -> str:
        return "<html><body><p>Crystal Intelligence PoC</p></body></html>"

    results = web_search(query="Crystal", fetcher=fake_fetch)

    assert len(results) == 1
    assert results[0]["content"].startswith("Crystal Intelligence")
    assert "url" in results[0]


def test_web_search_handles_failure() -> None:
    def fake_fetch(url: str) -> str:
        raise RuntimeError("network")

    results = web_search(query="Crystal", fetcher=fake_fetch)

    assert results == []
