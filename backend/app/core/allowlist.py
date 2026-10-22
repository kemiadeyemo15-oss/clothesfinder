"""Retailer trust layer. Loaded once; consulted at ingest and at rank time.

Retailer names arrive messy from a shopping API ("Cos", "MANGO",
"John Lewis & Partners"), so matching is normalised (case-insensitive, accent-
and punctuation-insensitive, with a leading "& " and a trailing "& partners"
stripped) rather than exact. The product keeps its real displayed name; only
the trust lookup is normalised.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_DATA = Path(__file__).resolve().parent.parent / "data" / "allowlist.json"


def _norm(s: str) -> str:
    s = s.lower().strip()
    s = re.sub(r"\.(com|co\.uk)\b", "", s)
    s = re.sub(r"[^a-z0-9& ]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s.startswith("& "):
        s = s[2:]
    s = re.sub(r" & partners$", "", s)
    s = re.sub(r" (uk|outlet|official|store)$", "", s)
    return s.strip()


class Allowlist:
    def __init__(self, allow: dict[str, dict], deny: list[str]):
        self.allow = allow
        self.deny = {_norm(d) for d in deny}
        # normalised key -> canonical retailer name
        self._norm_map = {_norm(k): k for k in allow}

    def canonical(self, retailer: str) -> str | None:
        """Resolve a messy retailer string to its allowlist key, or None."""
        n = _norm(retailer)
        if not n:
            return None
        if n in self._norm_map:
            return self._norm_map[n]
        # tolerate suffixes/prefixes: "john lewis & partners" -> "john lewis"
        for key_norm, key in self._norm_map.items():
            if n == key_norm or n.startswith(key_norm + " ") or key_norm.startswith(n + " "):
                return key
        return None

    def is_trusted(self, retailer: str) -> bool:
        return self.canonical(retailer) is not None and not self.is_denied(retailer)

    def is_denied(self, retailer: str) -> bool:
        return _norm(retailer) in self.deny

    def ship_days(self, retailer: str) -> int | None:
        key = self.canonical(retailer)
        return self.allow.get(key, {}).get("ship_days") if key else None

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
