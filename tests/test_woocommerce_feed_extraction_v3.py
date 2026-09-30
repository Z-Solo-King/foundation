import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "woocommerce_feed_extraction_v3.py"
SPEC = importlib.util.spec_from_file_location("woocommerce_feed_extraction_v3", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

valid_store_product = MODULE.valid_store_product
valid_native_google = MODULE.valid_native_google
feed_routes = MODULE.feed_routes

def test_valid_store_product_shape():
    assert valid_store_product({
        "id": 1, "name": "Test", "permalink": "https://example.com/product/test/",
        "prices": {"price": "1000", "currency_code": "INR"}
    })
    assert not valid_store_product({"id": 1, "name": "Test", "permalink": "https://example.com/p"})

def test_native_google_requires_fields_in_same_item():
    split = b'''<rss xmlns:g="http://base.google.com/ns/1.0"><channel>
    <item><g:id>1</g:id><g:title>A</g:title></item>
    <item><g:link>https://example.com/a</g:link><g:price>1 INR</g:price></item>
    </channel></rss>'''
    assert not valid_native_google(split, "application/xml")[0]

def test_route_discovery_finds_feed_routes():
    api = {"routes": {
        "/feedcraft-product-feed/v1/google.xml": {},
        "/wc/store/v1/products": {},
        "/foo/{id}/feed": {}
    }}
    out = feed_routes("https://example.com/wp-json/", api, "https://example.com")
    assert out == ["https://example.com/wp-json/feedcraft-product-feed/v1/google.xml"]
