import pytest

from tools.woocommerce_focus_google_feed_lab import (
    TARGETS,
    parse_wp_json_routes,
    safe_url,
    strategy_specs,
    validate_native_xml,
)


def test_scope_is_two_sites_only():
    assert TARGETS == (
        ("avikaretails", "https://www.avikaretails.com"),
        ("krgkart", "https://krgkart.com"),
    )


def test_exactly_100_named_strategies():
    specs = strategy_specs()
    assert len(specs) == 100
    assert [x[0] for x in specs] == [f"T{i:03d}" for i in range(1, 101)]
    assert len({x[0] for x in specs}) == 100


def test_native_google_xml_is_accepted():
    body = b'''<?xml version="1.0"?><rss xmlns:g="http://base.google.com/ns/1.0"><channel><item><g:id>SKU-1</g:id><g:title>Widget</g:title><g:link>https://example.test/p/1</g:link><g:price>1999 INR</g:price></item></channel></rss>'''
    result = validate_native_xml(body, "application/xml")
    assert result.valid is True
    assert result.product_items == 1
    assert result.google_fields >= 4


def test_sitemap_is_not_a_product_feed():
    body = b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://example.test/p/1</loc></url></urlset>'
    result = validate_native_xml(body, "application/xml")
    assert result.valid is False
    assert result.format == "sitemap"


def test_store_api_is_not_a_product_feed():
    result = validate_native_xml(b'{"products":[{"id":1,"name":"x","prices":{"price":"1999"}}]}', "application/json")
    assert result.valid is False


def test_external_candidate_allowed_but_private_ip_rejected():
    assert safe_url("https://feeds.example.test/google.xml", "https://krgkart.com", allow_external=True)
    assert safe_url("http://127.0.0.1/google.xml", "https://krgkart.com", allow_external=True) is None


def test_wp_json_route_discovery():
    payload = b'{"routes":{"/feedcraft-product-feed/v1/xml":{"methods":["GET"]},"/wc/store/v1/products":{"methods":["GET"]},"/google-feed/v1/xml":{"methods":["GET"]}}}'
    found = parse_wp_json_routes(payload, "https://example.test")
    assert "https://example.test/feedcraft-product-feed/v1/xml" in found
    assert "https://example.test/google-feed/v1/xml" in found
    assert "https://example.test/wc/store/v1/products" in found


@pytest.mark.parametrize("root", ["https://www.avikaretails.com", "https://krgkart.com"])
def test_target_roots_are_https(root):
    assert root.startswith("https://")
