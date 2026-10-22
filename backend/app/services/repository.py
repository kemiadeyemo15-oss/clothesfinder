"""Product repository — the pre-indexed retrieval path (for affiliate feeds).

Protocol + in-memory impl. The Postgres/pgvector impl lives in repository_pg.py
and is imported lazily (only when CF_REPO_BACKEND=postgres) so dev/test don't
need SQLAlchemy or a database.
"""
from __future__ import annotations

from typing import Protocol

from ..domain import Product
from .vectormath import cosine


class ProductRepository(Protocol):
    async def upsert(self, products: list[Product]) -> None: ...
    async def search(self, query_vec: list[float], limit: int) -> list[tuple[Product, float]]: ...
    async def count(self) -> int: ...


class InMemoryProductRepository:
    """Exact cosine over an in-memory list. Fine for dev and small catalogues."""

    def __init__(self) -> None:
        self._items: dict[str, Product] = {}

    async def upsert(self, products: list[Product]) -> None:
        for p in products:
            self._items[p.id] = p

    async def search(self, query_vec: list[float], limit: int) -> list[tuple[Product, float]]:
        scored = [
            (p, cosine(query_vec, p.embedding or []))
            for p in self._items.values()
        ]
        scored = [(p, s) for p, s in scored if s > 0]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:limit]

    async def count(self) -> int:
        return len(self._items)
