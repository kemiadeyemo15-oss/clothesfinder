"""FastAPI entrypoint.

    uvicorn app.main:app --reload
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .deps import build_search_service
from .api import routes_search, routes_health


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Build the search service once; share it across requests.
    app.state.search_service = await build_search_service()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="clothesfinder", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(routes_health.router)
    app.include_router(routes_search.router)
    return app


app = create_app()
