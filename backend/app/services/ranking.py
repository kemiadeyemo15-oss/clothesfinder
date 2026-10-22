"""Ranking — blend similarity with trust/shipping, apply hard filters.

Similarity leads; trust breaks ties and demotes slow shippers. Junk retailers
are already gone (allowlist at ingest), so this only needs to order the good."""
from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.allowlist import Allowlist
from ..domain import Product, ScoredProduct
from ..schemas import Attributes

if TYPE_CHECKING:
    from ..config import Settings


def rank(
    retrieved: list[tuple[Product, float]],
    attrs: Attributes,
    allowlist: Allowlist,
    settings: "Settings",
) -> list[ScoredProduct]:
    w = settings.trust_weight
    out: list[ScoredProduct] = []

    for product, sim in retrieved:
        # Hard filters (defensive; indexed retrievers may pre-filter).
        if attrs.price_max is not None and product.price > attrs.price_max:
            continue
        if attrs.category and product.category and product.category != attrs.category:
            continue
        if not allowlist.is_trusted(product.retailer):
            continue

        trust = allowlist.trust_score(product.retailer)
        ship = allowlist.ship_days(product.retailer)
        score = sim * (1 - w) + trust * w
        out.append(ScoredProduct(
            product=product,
            similarity=round(sim, 3),
            trust=round(trust, 2),
            ship_days=ship,
            score=round(score, 3),
        ))

    out.sort(key=lambda s: s.score, reverse=True)
    return out
