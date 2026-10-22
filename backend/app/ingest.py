"""Ingest job: inventory provider -> embed -> repository.

    python -m app.ingest "wool coat"      # pull candidates, embed, index

Run on a schedule (feeds) or on demand. In dev with the stub embedder + seed
inventory it's a no-network smoke of the whole ingest path.
"""
from __future__ import annotations

import asyncio
import sys

from .config import get_settings
from .core.allowlist import get_allowlist
from .services.embeddings import build_embedder
from .services.inventory import build_inventory
from .services.tagging import build_tagger


async def main(query: str) -> None:
    settings = get_settings()
    allowlist = get_allowlist()
    embedder = build_embedder(settings)
    inventory = build_inventory(settings, allowlist)
    tagger = build_tagger(settings)

    products = await inventory.fetch(query.split())
    for p in products:
        # Scan the product image into vocab attributes (vlm), or title (default).
        tags = await tagger.tag(p.title, image_url=(p.image if p.image != "unknown" else None))
        p.category = tags.category or p.category
        p.colours = tags.colours or p.colours
        p.materials = tags.materials or p.materials
        p.silhouettes = tags.silhouettes or p.silhouettes
        p.embedding = await embedder.embed_attributes(p.attributes())

    if settings.repo_backend == "postgres":
        from .services.repository_pg import PostgresProductRepository
        repo = PostgresProductRepository(settings)
        await repo.upsert(products)
        total = await repo.count()
        print(f"indexed {len(products)} products; {total} total in Postgres")
    else:
        print(f"[dev] embedded {len(products)} products (set CF_REPO_BACKEND=postgres to persist)")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "coat"))
