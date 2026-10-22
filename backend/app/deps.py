"""Dependency wiring. Builds the SearchService from config, choosing concrete
impls. The Postgres repository is imported lazily so dev/test never need
SQLAlchemy or a database."""
from __future__ import annotations

from .config import Settings, get_settings
from .core.allowlist import get_allowlist
from .services.embeddings import build_embedder
from .services.inventory import build_inventory
from .services.retrieval import LiveRetriever, IndexedRetriever, Retriever
from .services.search_service import SearchService


async def build_retriever(settings: Settings, allowlist, embedder) -> Retriever:
    if settings.repo_backend == "postgres":
        # Lazy import: only pulls SQLAlchemy/pgvector when actually using PG.
        from .services.repository_pg import PostgresProductRepository
        repo = PostgresProductRepository(settings)
        await repo.init()
        return IndexedRetriever(repo)
    inventory = build_inventory(settings, allowlist)
    return LiveRetriever(inventory, embedder)


async def build_search_service() -> SearchService:
    settings = get_settings()
    allowlist = get_allowlist()
    embedder = build_embedder(settings)
    retriever = await build_retriever(settings, allowlist, embedder)
    return SearchService(settings, allowlist, embedder, retriever)
