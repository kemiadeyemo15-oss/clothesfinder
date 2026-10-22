"""End-to-end API test over the default (stub/seed/in-memory) impls."""
import base64
import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["impls"]["inventory"] == "seed"


def test_text_search_ranks_expected_coat_top():
    r = client.post("/search", json={"text": "oversized cream wool coat under 200"})
    assert r.status_code == 200
    body = r.json()
    assert body["query"]["category"] == "coat"
    assert body["results"], "expected results"
    top = body["results"][0]["product"]
    assert top["retailer"] == "COS"
    assert top["price"] <= 200
    # junk retailers must never appear
    assert all(x["product"]["retailer"] not in {"SHEIN", "Temu"} for x in body["results"])


def test_image_plus_text_merges():
    img = Image.new("RGB", (120, 120), (236, 228, 206))
    buf = io.BytesIO(); img.save(buf, format="PNG")
    data_url = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    r = client.post("/search", json={"text": "oversized wool coat", "image": data_url})
    assert r.status_code == 200
    q = r.json()["query"]
    assert "cream" in q["colours"]       # colour came from the image
    assert q["category"] == "coat"       # category came from the text
