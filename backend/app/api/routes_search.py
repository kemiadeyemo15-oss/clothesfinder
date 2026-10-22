"""Search endpoint. Thin: validate in, call the service, map out."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import get_settings
from ..schemas import (
    SearchRequest, SearchResponse, ResultOut, ProductOut,
)

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(req: SearchRequest, request: Request) -> SearchResponse:
    settings = get_settings()
    service = request.app.state.search_service
    limit = min(req.limit or settings.max_results, settings.max_results)

    attrs, ranked, took_ms = await service.search(req.text, req.image, limit)

    results = [
        ResultOut(
            product=ProductOut(
                id=s.product.id, title=s.product.title, retailer=s.product.retailer,
                price=s.product.price, currency=s.product.currency,
                url=s.product.url, image=s.product.image, category=s.product.category,
            ),
            similarity=s.similarity, trust=s.trust,
            ship_days=s.ship_days, score=s.score,
        )
        for s in ranked
    ]
    return SearchResponse(query=attrs, results=results, took_ms=took_ms)
