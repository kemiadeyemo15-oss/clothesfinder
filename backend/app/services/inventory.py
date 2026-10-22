"""Inventory provider — where products come from.

The real bottleneck of the whole product. v1 wraps a shopping-search API and
filters to the allowlist; later you add affiliate feeds for economics. Both
implementations yield normalised `Product`s so ingest downstream is identical.

- SeedInventory: loads the bundled JSON. Dev/test, zero network.
- ShoppingApiInventory: queries a SerpApi-compatible shopping endpoint, drops
  anything not on the allowlist, normalises to Product. Fill the response
  mapping for your chosen provider at the TODO.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, TYPE_CHECKING

from ..core.allowlist import Allowlist
from ..domain import Product

if TYPE_CHECKING:
    from ..config import Settings

_SEED = Path(__file__).resolve().parent.parent / "data" / "seed_catalog.json"


class InventoryProvider(Protocol):
    async def fetch(self, query_terms: list[str]) -> list[Product]: ...


class SeedInventory:
    def __init__(self, allowlist: Allowlist):
        self.allowlist = allowlist
        raw = json.loads(_SEED.read_text())
        self._all = [
            Product(**{k: v for k, v in row.items() if not k.startswith("_")})
            for row in raw["products"]
        ]
        # Enforce allowlist at ingest.
        self._all = [p for p in self._all if self.allowlist.is_trusted(p.retailer)]

    async def fetch(self, query_terms: list[str]) -> list[Product]:
        return list(self._all)


class ShoppingApiInventory:
    def __init__(self, settings: "Settings", allowlist: Allowlist):
        self.url = settings.shopping_api_url
        self.key = settings.shopping_api_key
        self.allowlist = allowlist

    async def fetch(self, query_terms: list[str]) -> list[Product]:
        import httpx
        q = " ".join(query_terms) or "clothing"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.url,
                params={"q": q, "engine": "google_shopping", "api_key": self.key},
            )
            resp.raise_for_status()
            data = resp.json()

        # Tag each product's attributes from its title using the same rule
        # parser the query box uses, so the (stub) embedder has something to
        # match against. Real embeddings (Lykdat/CLIP) supersede this later.
        from .query import _parse_text_rules

        products: list[Product] = []
        for item in data.get("shopping_results", []):  # SerpApi google_shopping shape
            retailer = (item.get("source") or "").strip()
            if not self.allowlist.is_trusted(retailer):
                continue  # junk/untrusted excluded by construction
            title = item.get("title", "")
            tags = _parse_text_rules(title)
            products.append(
                Product(
                    id=str(item.get("product_id") or item.get("position")),
                    title=title,
                    retailer=retailer,
                    category=tags.category or "",
                    colours=tags.colours,
                    materials=tags.materials,
                    silhouettes=tags.silhouettes,
                    price=float(item.get("extracted_price") or 0.0),
                    url=item.get("product_link") or item.get("link") or "unknown",
                    image=item.get("thumbnail", "unknown"),
                )
            )
        return products


def build_inventory(settings: "Settings", allowlist: Allowlist) -> InventoryProvider:
    if settings.inventory == "shopping_api":
        return ShoppingApiInventory(settings, allowlist)
    return SeedInventory(allowlist)
