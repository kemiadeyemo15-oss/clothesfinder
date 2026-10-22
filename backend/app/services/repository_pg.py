"""Postgres + pgvector repository. Vector search runs in the database.

Imported lazily (see deps.build_retriever) so it's only required on the
Postgres path.
"""
from __future__ import annotations

from sqlalchemy import select, func

from ..config import Settings
from ..db import SessionLocal
from ..domain import Product
from ..models import ProductORM


def _to_domain(row: ProductORM, embedding: list[float] | None = None) -> Product:
    return Product(
        id=row.id, title=row.title, retailer=row.retailer, category=row.category,
        colours=list(row.colours or []), materials=list(row.materials or []),
        silhouettes=list(row.silhouettes or []), price=row.price,
        currency=row.currency, url=row.url, image=row.image, embedding=embedding,
    )


class PostgresProductRepository:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def init(self) -> None:
        # Extension + tables are created by alembic migrations in deployment;
        # nothing to do at runtime.
        return None

    async def upsert(self, products: list[Product]) -> None:
        async with SessionLocal() as session:
            for p in products:
                await session.merge(ProductORM(
                    id=p.id, title=p.title, retailer=p.retailer, category=p.category,
                    colours=p.colours, materials=p.materials, silhouettes=p.silhouettes,
                    price=p.price, currency=p.currency, url=p.url, image=p.image,
                    embedding=p.embedding or [0.0] * self.settings.embedding_dim,
                ))
            await session.commit()

    async def search(self, query_vec: list[float], limit: int) -> list[tuple[Product, float]]:
        # pgvector cosine distance; similarity = 1 - distance.
        dist = ProductORM.embedding.cosine_distance(query_vec)
        async with SessionLocal() as session:
            rows = (await session.execute(
                select(ProductORM, dist.label("distance")).order_by(dist).limit(limit)
            )).all()
        return [(_to_domain(r.ProductORM), 1.0 - float(r.distance)) for r in rows]

    async def count(self) -> int:
        async with SessionLocal() as session:
            return int((await session.execute(select(func.count(ProductORM.id)))).scalar() or 0)
