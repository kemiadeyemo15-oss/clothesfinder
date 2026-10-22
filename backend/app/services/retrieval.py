"""Retrieval — getting candidate products + their similarity to the query.

Two real architectures, both behind one Protocol:

- LiveRetriever: query-time. Calls the inventory provider (shopping API / seed),
  embeds each candidate, scores cosine. This is the v1 path — it needs no
  pre-built index, which is why it pairs with the shopping-search API.

- IndexedRetriever: queries a pre-embedded repository (pgvector). This is the
  path you move to once affiliate feeds are ingested offline; it scales to large
  catalogues because the vector search runs in the database.
"""
from __future__ import annotations

from typing import Protocol

from ..schemas import Attributes
from ..domain import Product
from .embeddings import Embedder
from .inventory import InventoryProvider
from .repository import ProductRepository
from .vectormath import cosine


class Retriever(Protocol):
    async def retrieve(
        self, query_vec: list[float], attrs: Attributes, limit: int
    ) -> list[tuple[Product, float]]: ...


class LiveRetriever:
    def __init__(self, inventory: InventoryProvider, embedder: Embedder):
        self.inventory = inventory
        self.embedder = embedder

    async def retrieve(self, query_vec, attrs, limit):
        candidates = await self.inventory.fetch(attrs.tokens())
        scored: list[tuple[Product, float]] = []
        for p in candidates:
            vec = p.embedding or await self.embedder.embed_attributes(p.attributes())
            scored.append((p, cosine(query_vec, vec)))
        scored = [(p, s) for p, s in scored if s > 0]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:limit]


class IndexedRetriever:
    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def retrieve(self, query_vec, attrs, limit):
        return await self.repository.search(query_vec, limit)
