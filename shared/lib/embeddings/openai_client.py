"""Wrapper around OpenAI embedding API with simple retry support."""
from __future__ import annotations

import logging
from typing import Iterable, List

from openai import OpenAI

from config.settings import get_settings
from retry.backoff import run_with_backoff


LOGGER = logging.getLogger(__name__)


class EmbeddingClient:
    """Client responsible for generating embeddings for knowledge content."""

    def __init__(self, model: str = "text-embedding-3-small") -> None:
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._model = model

    def embed(self, texts: Iterable[str]) -> List[List[float]]:
        def _call() -> List[List[float]]:
            response = self._client.embeddings.create(model=self._model, input=list(texts))
            return [data.embedding for data in response.data]

        return run_with_backoff(
            _call,
            logger=LOGGER,
            attempts=3,
            base_delay=1,
        )


_default_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _default_client
    if _default_client is None:
        _default_client = EmbeddingClient()
    return _default_client
