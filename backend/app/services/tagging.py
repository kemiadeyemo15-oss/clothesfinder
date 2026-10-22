"""Attribute tagging — turn a product into structured vocab attributes.

Two implementations behind one interface:

- TitleTagger: parses the product title with the rule parser. Cheap, offline,
  the default. Good enough to rank, limited by what the title says.
- VlmTagger: a VISION model reads the product IMAGE and returns attributes in
  the controlled vocab. High accuracy for category / colour / silhouette;
  material is taken from the image only when confident, else from the title.

WHERE TO RUN IT: at INGEST, once per product (see app/ingest.py) — never per
query. Scanning a page of results on every search is slow and expensive; tag
once when the product enters the catalogue and store the result.

=== SWAP POINT ===
VlmTagger targets an Anthropic-style Messages vision API by default. Set the
key, and confirm the current model name, in config. Any vision/LLM provider
works — keep `tag()` returning an Attributes and nothing downstream changes.
A failed or low-confidence scan falls back to the title tags, so ingest never
hard-fails on one bad image.
"""
from __future__ import annotations

import base64
import json
from typing import Protocol, TYPE_CHECKING

from ..core.vocab import CATEGORIES, COLOURS, MATERIALS, SILHOUETTES
from ..schemas import Attributes
from .query import _parse_text_rules

if TYPE_CHECKING:
    from ..config import Settings


class AttributeTagger(Protocol):
    async def tag(
        self, title: str, image_bytes: bytes | None = None, image_url: str | None = None
    ) -> Attributes: ...


class TitleTagger:
    """Default: attributes from the title. No network."""

    async def tag(self, title, image_bytes=None, image_url=None) -> Attributes:
        return _parse_text_rules(title)


def _build_prompt() -> str:
    return (
        "You are tagging a single clothing product from its photo. "
        "Return ONLY a JSON object with these keys and no prose:\n"
        f'  "category": one of {CATEGORIES} or null\n'
        f'  "colours": a subset of {COLOURS}\n'
        f'  "materials": a subset of {MATERIALS} — ONLY if visually confident, else []\n'
        f'  "silhouettes": a subset of {SILHOUETTES}\n'
        "Use only values from these lists. Omit anything you are unsure of."
    )


class VlmTagger:
    """Vision-model tagging into the controlled vocab, with title fallback."""

    def __init__(self, settings: "Settings"):
        self.key = settings.vision_api_key
        self.model = settings.vision_model
        self.url = settings.vision_base_url

    async def tag(self, title, image_bytes=None, image_url=None) -> Attributes:
        fallback = _parse_text_rules(title)
        try:
            if image_bytes is None and image_url:
                image_bytes = await self._fetch(image_url)
            if not image_bytes:
                return fallback
            raw = await self._scan(image_bytes)
            tagged = self._coerce(raw)
            # Merge: vision leads; title fills anything the scan left blank.
            return tagged.merge(fallback)
        except Exception:
            # One bad image must never break an ingest run.
            return fallback

    async def _fetch(self, url: str) -> bytes | None:
        import httpx
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.content

    async def _scan(self, image_bytes: bytes) -> dict:
        import httpx
        b64 = base64.standard_b64encode(image_bytes).decode()
        body = {
            "model": self.model,
            "max_tokens": 300,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {
                            "type": "base64", "media_type": "image/jpeg", "data": b64}},
                        {"type": "text", "text": _build_prompt()},
                    ],
                }
            ],
        }
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                self.url,
                headers={"x-api-key": self.key,
                         "anthropic-version": "2023-06-01",
                         "content-type": "application/json"},
                json=body,
            )
            r.raise_for_status()
            data = r.json()
        # Anthropic Messages: text lives in content[0].text
        text = data["content"][0]["text"]
        return self._extract_json(text)

    @staticmethod
    def _extract_json(text: str) -> dict:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end == -1:
            return {}
        return json.loads(text[start:end + 1])

    @staticmethod
    def _coerce(raw: dict) -> Attributes:
        def keep(vals, allowed):
            return [v for v in (vals or []) if v in allowed]
        cat = raw.get("category")
        return Attributes(
            category=cat if cat in CATEGORIES else None,
            colours=keep(raw.get("colours"), COLOURS),
            materials=keep(raw.get("materials"), MATERIALS),
            silhouettes=keep(raw.get("silhouettes"), SILHOUETTES),
        )


def build_tagger(settings: "Settings") -> AttributeTagger:
    if settings.tagger == "vlm":
        return VlmTagger(settings)
    return TitleTagger()
