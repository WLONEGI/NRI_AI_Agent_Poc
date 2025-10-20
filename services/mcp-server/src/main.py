"""FastAPI application entrypoint for the MCP server."""
from __future__ import annotations

import logging
from typing import Dict

from fastapi import FastAPI, HTTPException

from apis import batch_api, query_api, search_api
from infra.neo4j_client import health_check as neo4j_health_check
from logging_config import configure_logging


LOGGER = logging.getLogger(__name__)


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title="Crystal Intelligence MCP Server",
        version="0.1.0",
        description="LangGraph agent + Neo4j knowledge orchestration APIs",
    )

    app.include_router(query_api.router)
    app.include_router(search_api.router)
    app.include_router(batch_api.router)

    @app.get("/healthz")
    async def healthz() -> Dict[str, str]:
        try:
            healthy = neo4j_health_check()
        except Exception as exc:  # pragma: no cover - defensive safety
            LOGGER.exception("Health check failed")
            raise HTTPException(status_code=503, detail=str(exc)) from exc

        if not healthy:
            raise HTTPException(status_code=503, detail="Neo4j unavailable")

        return {"status": "ok", "neo4j": "ok"}

    return app


app = create_app()

