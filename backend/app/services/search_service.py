"""SearchService — the one orchestrator the API calls.

    parse(text,image) -> Attributes -> embed -> retrieve -> rank -> results

Wired once at startup with concrete impls chosen by config, so routes stay thin
and everything is swappable without touching this flow.
"""
from __future__ import annotations

import base64
import time
from typing import TYPE_CHECKING

from ..core.allowlist import Allowlist
from ..domain import ScoredProduct
from ..schemas import Attributes
from .embeddings import Embedder
from .ranking import rank
from .retrieval import Retriever
from . import query as query_mod

if TYPE_CHECKING:
    from ..config import Settings


class SearchService:
    def __init__(
        self,
        settings: "Settings",
        allowlist: Allowlist,
        embedder: Embedder,
        retriever: Retriever,
    ):
        self.settings = settings
        self.allowlist = allowlist
        self.embedder = embedder
        self.retriever = retriever

    async def _load_image_bytes(self, image: str) -> bytes | None:
        if image.startswith("data:") and "," in image:
            return base64.b64decode(image.split(",", 1)[1])
        if image.startswith("http"):
            import httpx
            async with httpx.AsyncClient(timeout=10) as c:
                r = await c.get(image)
                r.raise_for_status()
                return r.content
        return None

    async def search(
        self, text: str | None, image: str | None, limit: int
    ) -> tuple[Attributes, list[ScoredProduct], int]:
        t0 = time.perf_counter()
        attrs = Attributes()

        if text:
            attrs = attrs.merge(query_mod.parse_text(text, self.settings))

        image_vec: list[float] | None = None
        if image:
            img_bytes = await self._load_image_bytes(image)
            if img_bytes:
                for c in query_mod.colours_from_image(img_bytes):
                    if c not in attrs.colours:
                        attrs.colours.append(c)
                # In prod, the embedder also yields an image-side vector.
                if self.settings.embedder != "stub":
                    image_vec = await self.embedder.embed_image(img_bytes)

        query_vec = await self.embedder.embed_attributes(attrs)
        # If we have a real image vector, average it with the text-attr vector
        # (both are in the same space) for a true multimodal query.
        if image_vec and len(image_vec) == len(query_vec):
            query_vec = [(a + b) / 2 for a, b in zip(query_vec, image_vec)]

        retrieved = await self.retriever.retrieve(query_vec, attrs, limit * 3)
        ranked = rank(retrieved, attrs, self.allowlist, self.settings)[:limit]
        took_ms = int((time.perf_counter() - t0) * 1000)
        return attrs, ranked, took_ms
