"""ORM models. pgvector column holds the product image embedding."""
from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import String, Float, Integer, ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from .config import get_settings
from .db import Base

_DIM = get_settings().embedding_dim


class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    retailer: Mapped[str] = mapped_column(String, index=True)
    category: Mapped[str] = mapped_column(String, default="")
    colours: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    materials: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    silhouettes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    price: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String, default="GBP")
    url: Mapped[str] = mapped_column(String, default="unknown")
    image: Mapped[str] = mapped_column(String, default="unknown")
    embedding: Mapped[list[float]] = mapped_column(Vector(_DIM))
