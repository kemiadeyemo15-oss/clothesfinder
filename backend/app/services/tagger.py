"""Tagger — turn a product (image + title + description) into structured tags.

This is what makes matching accurate: a vision model looks at the product PHOTO
as primary evidence and uses the title/description to confirm details it can't
see (fabric, exact colour name), then emits attributes locked to the controlled
vocabulary. Those tags drive the embedding + ranking.

- RulesTagger: offline keyword parse of title+description. Fast, no cost, crude.
- VlmTagger: a real visual scan via Claude vision. Accurate; one API call per
  product, so results are CACHED (a product's photo doesn't change) and it
  degrades to the rule parse on any error, so the pipeline never hard-fails.

Config picks which (CF_TAGGER). Caching is keyed by product id across requests.
"""
from __future__ import annotations

import json
import re
from typing import Protocol, TYPE_CHECKING

from ..core.vocab import CATEGORIES, COLOURS, MATERIALS, SILHOUETTES
from ..schemas import Attributes
from .query import _parse_text_rules

if TYPE_CHECKING:
    from ..config import Settings


class Tagger(Protocol):
    async def tag(
        self, *, product_id: str, title: str, description: str = "",
        image_url: str | None = None,
    ) -> Attributes: ...


# --- rules (offline) -------------------------------------------------------
class RulesTagger:
    async def tag(self, *, product_id, title, description="", image_url=None) -> Attributes:
        return _parse_text_rules(f"{title} {description}")


# --- vision model (accurate) ----------------------------------------------
_VLM_PROMPT = f"""You are tagging a clothing product for a fashion search engine.
Look at the product IMAGE as the primary evidence. Use the title and description \
to confirm details the image cannot show (fabric, precise colour name).

Return ONLY a JSON object with these keys, using ONLY the allowed values. Omit a \
value if you are not confident; never invent one outside the lists.

category (pick at most ONE): {CATEGORIES}
colours (list, the garment's own colours): {COLOURS}
materials (list): {MATERIALS}
silhouettes (list, fit/cut/length): {SILHOUETTES}

Respond with the JSON object and nothing else."""


class VlmTagger:
    """Visual + text tagging via the Anthropic Messages API (Claude vision)."""

    def __init__(self, settings: "Settings"):
        self.key = settings.llm_api_key
        self.model = settings.llm_model
        self._cache: dict[str, Attributes] = {}
        self._fallback = RulesTagger()

    async def tag(self, *, product_id, title, description="", image_url=None) -> Attributes:
        if product_id in self._cache:
            return self._cache[product_id]
        try:
            attrs = await self._scan(title, description, image_url)
        except Exception:
            # Never hard-fail a search because one tag call errored.
            attrs = await self._fallback.tag(
                product_id=product_id, title=title, description=description
            )
        self._cache[product_id] = attrs
        return attrs

    async def _scan(self, title, description, image_url) -> Attributes:
        import httpx

        content: list[dict] = []
        if image_url and image_url != "unknown" and image_url.startswith("http"):
            content.append({"type": "image", "source": {"type": "url", "url": image_url}})
        text = f"Title: {title}\nDescription: {description or '(none)'}\n\n{_VLM_PROMPT}"
        content.append({"type": "text", "text": text})

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 300,
                    "temperature": 0,
                    "messages": [{"role": "user", "content": content}],
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw = "".join(b.get("text", "") for b in data.get("content", []))
        return _coerce_attributes(raw)


def _coerce_attributes(raw: str) -> Attributes:
    """Parse the model's JSON and keep only in-vocabulary values."""
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    obj = json.loads(m.group(0)) if m else {}

    def keep(values, allowed):
        if isinstance(values, str):
            values = [values]
        return [v for v in (values or []) if v in allowed]

    cat = obj.get("category")
    cat = cat if cat in CATEGORIES else None
    return Attributes(
        category=cat,
        colours=keep(obj.get("colours"), COLOURS),
        materials=keep(obj.get("materials"), MATERIALS),
        silhouettes=keep(obj.get("silhouettes"), SILHOUETTES),
    )


def build_tagger(settings: "Settings") -> Tagger:
    if settings.tagger == "vlm":
        return VlmTagger(settings)
    return RulesTagger()
