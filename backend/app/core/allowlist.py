"""Retailer trust layer. Loaded once; consulted at ingest and at rank time."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "allowlist.json"


class Allowlist:
    def __init__(self, allow: dict[str, dict], deny: list[str]):
        self.allow = allow
        self.deny = {d.lower() for d in deny}

    def is_trusted(self, retailer: str) -> bool:
        return retailer in self.allow

    def is_denied(self, retailer: str) -> bool:
        return retailer.lower() in self.deny

    def ship_days(self, retailer: str) -> int | None:
        return self.allow.get(retailer, {}).get("ship_days")

    def trust_score(self, retailer: str) -> float:
        """0..1 from shipping speed. 2 days ~1.0, 7 days ~0.3, untrusted 0."""
        d = self.ship_days(retailer)
        if d is None:
            return 0.0
        return max(0.0, min(1.0, 1.0 - (d - 2) / 8))


@lru_cache
def get_allowlist() -> Allowlist:
    raw = json.loads(_DATA.read_text())
    return Allowlist(raw["allow"], raw["deny"])
