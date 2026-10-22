"""Query understanding: text and/or image -> Attributes.

Both paths converge to the same Attributes object, which is then embedded.

- Text: rule parser (dev) over the controlled vocab; LLM parser (prod) behind
  the same function signature. The LLM handles negation, occasion->attribute,
  and messy phrasing the rules can't.
- Image: real dominant-colour extraction (Pillow); category/material/silhouette
  come from the embedding model's attribute tagging in prod (TODO marked).
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from ..core.vocab import CATEGORIES, COLOURS, MATERIALS, SILHOUETTES
from ..schemas import Attributes

if TYPE_CHECKING:
    from ..config import Settings

_SYNONYMS = {
    "sweater": "jumper", "pullover": "jumper", "pants": "trousers",
    "slacks": "trousers", "sneakers": "trainers", "ecru": "cream",
    "off-white": "cream", "ivory": "cream", "khaki": "olive",
    "baggy": "oversized", "loose": "relaxed",
}

_COLOUR_RGB = {
    "black": (20, 20, 20), "white": (245, 245, 245), "cream": (238, 230, 210),
    "beige": (214, 197, 170), "brown": (110, 78, 52), "tan": (190, 150, 110),
    "camel": (193, 154, 107), "grey": (128, 128, 128), "navy": (30, 40, 80),
    "blue": (50, 90, 180), "green": (60, 120, 70), "olive": (110, 110, 60),
    "red": (180, 50, 50), "burgundy": (110, 30, 50), "pink": (225, 160, 185),
    "purple": (120, 70, 150), "yellow": (220, 200, 70), "orange": (220, 130, 50),
}


def _find(terms: list[str], text: str) -> list[str]:
    return [t for t in terms if re.search(rf"\b{re.escape(t)}\b", text)]


def parse_text(query: str, settings: "Settings") -> Attributes:
    if settings.query_parser == "llm":
        return _parse_text_llm(query, settings)
    return _parse_text_rules(query)


def _parse_text_rules(query: str) -> Attributes:
    q = query.lower()
    for syn, canon in _SYNONYMS.items():
        if re.search(rf"\b{re.escape(syn)}\b", q):
            q += " " + canon
    cats = _find(CATEGORIES, q)
    attrs = Attributes(
        category=cats[0] if cats else None,
        colours=_find(COLOURS, q),
        materials=_find(MATERIALS, q),
        silhouettes=_find(SILHOUETTES, q),
    )
    m = re.search(r"(?:under|below|<|max|up to)\s*£?\s*(\d+)", q) or re.search(r"£\s*(\d+)", q)
    if m:
        attrs.price_max = float(m.group(1))
    return attrs


def _parse_text_llm(query: str, settings: "Settings") -> Attributes:
    # TODO: one call to your LLM asking for the Attributes JSON for `query`.
    # Keep it returning an Attributes; the rest of the pipeline is unchanged.
    # Falls back to rules until wired so the app never hard-fails.
    return _parse_text_rules(query)


def colours_from_image(image_bytes: bytes) -> list[str]:
    """Real dominant-colour extraction. Returns up to 2 nearest vocab colours."""
    try:
        import io
        from PIL import Image
    except Exception:
        return []
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((100, 100))
    w, h = img.size
    box = img.crop((w // 4, h // 4, 3 * w // 4, 3 * h // 4))
    pixels = [p for p in box.getdata() if 60 < sum(p) < 700] or list(box.getdata())
    avg = tuple(sum(c) // len(pixels) for c in zip(*pixels))

    def dist(name):
        return sum((a - b) ** 2 for a, b in zip(avg, _COLOUR_RGB[name]))

    return sorted(_COLOUR_RGB, key=dist)[:2]
