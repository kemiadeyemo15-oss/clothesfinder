"""Framework-free domain types shared across services (no SQLAlchemy import)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .schemas import Attributes


@dataclass
class Product:
    id: str
    title: str
    retailer: str
    category: str
    colours: list[str]
    materials: list[str]
    silhouettes: list[str]
    price: float
    currency: str = "GBP"
    url: str = "unknown"
    image: str = "unknown"
    embedding: list[float] | None = None

    def attributes(self) -> Attributes:
        return Attributes(
            category=self.category,
            colours=list(self.colours),
            materials=list(self.materials),
            silhouettes=list(self.silhouettes),
        )


@dataclass
class ScoredProduct:
    product: Product
    similarity: float
    trust: float
    ship_days: int | None
    score: float
