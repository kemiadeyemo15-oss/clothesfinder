from app.config import get_settings
from app.services.query import parse_text, colours_from_image


def test_parse_text_extracts_attributes():
    a = parse_text("oversized cream wool coat under £200", get_settings())
    assert a.category == "coat"
    assert "cream" in a.colours
    assert "wool" in a.materials
    assert "oversized" in a.silhouettes
    assert a.price_max == 200.0


def test_parse_text_synonyms():
    a = parse_text("baggy sweater", get_settings())
    assert a.category == "jumper"          # sweater -> jumper
    assert "oversized" in a.silhouettes    # baggy -> oversized


def test_colours_from_image_reads_dominant_colour():
    from PIL import Image
    import io
    img = Image.new("RGB", (120, 120), (255, 255, 255))
    for x in range(30, 90):
        for y in range(30, 90):
            img.putpixel((x, y), (236, 228, 206))  # cream block
    buf = io.BytesIO(); img.save(buf, format="PNG")
    cols = colours_from_image(buf.getvalue())
    assert "cream" in cols
