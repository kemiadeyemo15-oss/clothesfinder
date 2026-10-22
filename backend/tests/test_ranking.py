from app.config import get_settings
from app.core.allowlist import get_allowlist
from app.domain import Product
from app.schemas import Attributes
from app.services.ranking import rank


def _p(pid, retailer, price, category="coat"):
    return Product(id=pid, title=pid, retailer=retailer, category=category,
                   colours=[], materials=[], silhouettes=[], price=price)


def test_price_ceiling_filters():
    al, s = get_allowlist(), get_settings()
    retrieved = [(_p("a", "COS", 300), 0.9), (_p("b", "COS", 100), 0.9)]
    out = rank(retrieved, Attributes(price_max=150), al, s)
    assert [r.product.id for r in out] == ["b"]


def test_denied_retailer_never_ranks():
    al, s = get_allowlist(), get_settings()
    retrieved = [(_p("junk", "SHEIN", 10), 0.99), (_p("good", "COS", 100), 0.5)]
    out = rank(retrieved, Attributes(), al, s)
    assert [r.product.id for r in out] == ["good"]


def test_trust_breaks_ties_toward_faster_shipping():
    al, s = get_allowlist(), get_settings()
    retrieved = [(_p("slow", "Everlane", 100), 0.8), (_p("fast", "John Lewis", 100), 0.8)]
    out = rank(retrieved, Attributes(), al, s)
    assert out[0].product.id == "fast"   # same similarity, faster wins
