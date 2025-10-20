"""Web search tool using simple HTTP fetcher."""
from __future__ import annotations

import logging
from typing import Callable, List, Dict

try:
    import requests
except ImportError:  # pragma: no cover - requests optional
    requests = None

LOGGER = logging.getLogger(__name__)


def web_search(
    *,
    query: str,
    fetcher: Callable[[str], str] | None = None,
) -> List[Dict[str, str]]:
    fetcher = fetcher or _default_fetcher
    url = f"https://duckduckgo.com/?q={query}"
    try:
        html = fetcher(url)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("web_search fetch failed", exc_info=exc)
        return []
    text = _strip_html(html)
    return [{"url": url, "content": text}]


def _default_fetcher(url: str) -> str:
    if requests is None:  # pragma: no cover
        raise RuntimeError("requests not installed")
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    return response.text


def _strip_html(html: str) -> str:
    import re

    text = re.sub(r"<[^>]+>", " ", html)
    return " ".join(text.split())
