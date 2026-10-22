"""Controlled garment vocabulary — the contract both query paths resolve to.

In production this is seeded from your catalogue taxonomy and extended over
time; keeping it explicit keeps the stub embedder and the rule parser aligned.
"""
from __future__ import annotations

CATEGORIES = [
    "coat", "jacket", "blazer", "knit", "jumper", "cardigan", "shirt",
    "blouse", "t-shirt", "dress", "skirt", "trousers", "jeans", "shorts",
    "boots", "trainers", "heels", "bag",
]

COLOURS = [
    "black", "white", "cream", "beige", "brown", "tan", "camel", "grey",
    "navy", "blue", "green", "olive", "red", "burgundy", "pink", "purple",
    "yellow", "orange",
]

MATERIALS = [
    "wool", "cotton", "linen", "silk", "cashmere", "leather", "suede",
    "denim", "corduroy", "knit", "satin", "velvet",
]

SILHOUETTES = [
    "oversized", "relaxed", "fitted", "cropped", "longline", "tailored",
    "a-line", "wide-leg", "straight", "slim", "belted", "double-breasted",
    "collarless", "high-waisted", "midi", "maxi", "mini",
]

VOCAB = CATEGORIES + COLOURS + MATERIALS + SILHOUETTES
VOCAB_INDEX = {term: i for i, term in enumerate(VOCAB)}
