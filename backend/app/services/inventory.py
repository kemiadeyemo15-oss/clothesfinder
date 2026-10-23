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

import asyncio
import json
from pathlib import Path
from typing import Protocol, TYPE_CHECKING

from ..core.allowlist import Allowlist
from ..domain import Product
from .tagger import Tagger, RulesTagger

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
    def __init__(self, settings: "Settings", allowlist: Allowlist, tagger: Tagger | None = None):
        self.url = settings.shopping_api_url
        self.key = settings.shopping_api_key
        self.allowlist = allowlist
        self.tagger = tagger or RulesTagger()
        # Bound concurrent tag calls so a visual scan of ~60 products doesn't
        # open 60 simultaneous connections to the vision API.
        self._sem = asyncio.Semaphore(8)

    async def fetch(self, query_terms: list[str]) -> list[Product]:
        import httpx
        q = " ".join(query_terms) or "clothing"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(
                self.url,
                params={
                    "q": q, "engine": "google_shopping", "api_key": self.key,
                    # UK locale: UK retailers and GBP prices (SerpApi defaults to US).
                    "google_domain": "google.co.uk", "gl": "uk", "hl": "en",
                    "location": "United Kingdom",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        raw_items = [
            item for item in data.get("shopping_results", [])  # SerpApi google_shopping shape
            if self.allowlist.is_trusted((item.get("source") or "").strip())
        ]
        # Tag every trusted product (visual scan when CF_TAGGER=vlm, else the
        # rule parse). Concurrent + cached inside the tagger.
        products = await asyncio.gather(*(self._to_product(i) for i in raw_items))
        return list(products)

    async def _to_product(self, item: dict) -> Product:
        title = item.get("title", "")
        pid = str(item.get("product_id") or item.get("position"))
        image = item.get("thumbnail", "unknown")
        async with self._sem:
            tags = await self.tagger.tag(
                product_id=pid, title=title,
                description=item.get("snippet", ""), image_url=image,
            )
        return Product(
            id=pid, title=title,
            retailer=(item.get("source") or "").strip(),
            category=tags.category or "",
            colours=tags.colours, materials=tags.materials, silhouettes=tags.silhouettes,
            price=float(item.get("extracted_price") or 0.0),
            url=item.get("product_link") or item.get("link") or "unknown",
            currency=_currency(item.get("price") or ""),
            image=image,
        )


_SYMBOLS = {"£": "GBP", "$": "USD", "€": "EUR"}


def _currency(price_text: str) -> str:
    """SerpApi gives price as display text, e.g. "£45.00". Read the symbol."""
    for sym, code in _SYMBOLS.items():
        if sym in price_text:
            return code
    return "GBP"


def build_inventory(
    settings: "Settings", allowlist: Allowlist, tagger: Tagger | None = None
) -> InventoryProvider:
    if settings.inventory == "shopping_api":
        return ShoppingApiInventory(settings, allowlist, tagger)
    return SeedInventory(allowlist)
