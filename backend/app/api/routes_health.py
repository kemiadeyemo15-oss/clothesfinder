"""Liveness + a config echo for debugging which impls are active."""
from __future__ import annotations

from fastapi import APIRouter

from ..config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    s = get_settings()
    return {
        "status": "ok",
        "env": s.env,
        "impls": {
            "repo_backend": s.repo_backend,
            "embedder": s.embedder,
            "inventory": s.inventory,
            "query_parser": s.query_parser,
        },
    }
