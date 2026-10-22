"""API request/response models + the internal Attributes type."""
from __future__ import annotations

from pydantic import BaseModel, Field

from .core.vocab import VOCAB_INDEX


class Attributes(BaseModel):
    """Structured garment description — the common currency of the pipeline."""
    category: str | None = None
    colours: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    silhouettes: list[str] = Field(default_factory=list)
    price_max: float | None = None

    def tokens(self) -> list[str]:
        toks: list[str] = []
        if self.category:
            toks.append(self.category)
        toks += self.colours + self.materials + self.silhouettes
        return [t for t in toks if t in VOCAB_INDEX]

    def merge(self, other: "Attributes") -> "Attributes":
        return Attributes(
            category=self.category or other.category,
            colours=list(dict.fromkeys(self.colours + other.colours)),
            materials=list(dict.fromkeys(self.materials + other.materials)),
            silhouettes=list(dict.fromkeys(self.silhouettes + other.silhouettes)),
            price_max=self.price_max if self.price_max is not None else other.price_max,
        )


class SearchRequest(BaseModel):
    text: str | None = None
    image: str | None = None            # data URL (base64) or https URL
    limit: int | None = None


class ProductOut(BaseModel):
    id: str
    title: str
    retailer: str
    price: float
    currency: str = "GBP"
    url: str = "unknown"
    image: str = "unknown"
    category: str | None = None


class ResultOut(BaseModel):
    product: ProductOut
    similarity: float
    trust: float
    ship_days: int | None
    score: float


class SearchResponse(BaseModel):
    query: Attributes
    results: list[ResultOut]
    took_ms: int
