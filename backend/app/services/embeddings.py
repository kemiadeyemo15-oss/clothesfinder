"""Embedder — text and image into ONE vector space.

The interface is two methods returning `list[float]` of length `embedding_dim`.
Products are embedded from their IMAGE at ingest; queries from text and/or an
uploaded image. Because both land in one space, a typed query and a photo are
directly comparable to the same product vectors — that's the point of a
multimodal model.

- StubEmbedder: deterministic, offline. Embeds the controlled-vocab attributes
  as a multi-hot so dev/test returns sensible results with no model.
- LykdatEmbedder: calls a hosted fashion visual-search API. Fill in the exact
  request/response shape from Lykdat's docs when you wire your key — the TODOs
  mark precisely where.
"""
from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from ..core.vocab import VOCAB, VOCAB_INDEX
from ..schemas import Attributes

if TYPE_CHECKING:
    from ..config import Settings


class Embedder(Protocol):
    async def embed_attributes(self, attrs: Attributes) -> list[float]: ...
    async def embed_image(self, image_bytes: bytes) -> list[float]: ...


# --- stub (dev/test, no network) ------------------------------------------
class StubEmbedder:
    dim = len(VOCAB)

    async def embed_attributes(self, attrs: Attributes) -> list[float]:
        vec = [0.0] * self.dim
        for tok in attrs.tokens():
            vec[VOCAB_INDEX[tok]] = 1.0
        return vec

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        # Stub can't see; colour is extracted upstream in query.py and passed
        # as attributes. Return an empty vector so ranking leans on attributes.
        return [0.0] * self.dim


# --- real (hosted fashion API) --------------------------------------------
class LykdatEmbedder:
    def __init__(self, settings: "Settings"):
        self.key = settings.lykdat_api_key
        self.base = settings.lykdat_base_url
        self.dim = settings.embedding_dim

    async def embed_attributes(self, attrs: Attributes) -> list[float]:
        # Text side: send the reconstructed description as a text query.
        text = " ".join(attrs.tokens())
        return await self._embed_text(text)

    async def embed_image(self, image_bytes: bytes) -> list[float]:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self.base}/global/search",  # TODO: confirm endpoint in docs
                headers={"x-api-key": self.key},
                files={"image": ("q.jpg", image_bytes)},
            )
            resp.raise_for_status()
            data = resp.json()
        # TODO: map the response to a vector. If the API returns matches rather
        # than a raw embedding, either (a) use a /encode endpoint if offered, or
        # (b) switch to self-hosted CLIP to get vectors directly. See README.
        return self._coerce_vector(data)

    async def _embed_text(self, text: str) -> list[float]:
        import httpx
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self.base}/text/encode",   # TODO: confirm endpoint in docs
                headers={"x-api-key": self.key},
                json={"text": text},
            )
            resp.raise_for_status()
            return self._coerce_vector(resp.json())

    def _coerce_vector(self, data: dict) -> list[float]:
        vec = data.get("embedding") or data.get("vector")
        if not isinstance(vec, list):
            raise ValueError("embedding API response missing vector; map it here")
        return vec


def build_embedder(settings: "Settings") -> Embedder:
    if settings.embedder == "lykdat":
        return LykdatEmbedder(settings)
    return StubEmbedder()
