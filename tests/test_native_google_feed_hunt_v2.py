from pathlib import Path
import sys

from tools.native_google_feed_hunt_v2 import _cookie_header_from_netscape
from tools.native_google_feed_hunt_v2 import _public_json_lines
from tools.native_google_feed_hunt_v2 import wp_media_feed_candidates
from tools.native_google_feed_hunt_v2 import ctxfeed_urls, feed_priority, generated_upload_feed_candidates
from tools.native_google_feed_hunt_v2 import extract_explicit_feed_urls, extract_urls, validate_xml
from tools.native_google_feed_hunt_v2 import load_learned_feed_patterns, validation_candidate_groups

GOOD = b'''<?xml version="1.0"?><rss xmlns:g="http://base.google.com/ns/1.0"><channel><item><g:id>SKU</g:id><g:title>Widget</g:title><g:link>https://example.test/p/1</g:link><g:price>1999 INR</g:price></item></channel></rss>'''

def test_strict_native_validation():
    result = validate_xml(GOOD, "application/xml")
    assert result.valid is True
    assert result.product_items == 1
    assert result.google_fields >= 4

def test_sitemap_rejected():
    result = validate_xml(b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>x</loc></url></urlset>', "application/xml")
    assert result.valid is False
    assert result.format == "sitemap"

def test_generic_rss_rejected():
    result = validate_xml(b'<rss><channel><item><title>x</title><link>x</link></item></channel></rss>', "application/rss+xml")
    assert result.valid is False

def test_html_discovery_is_same_host_only():
    found = extract_urls('<a href="/wp-content/uploads/woo-feed/google/xml/google-shopping.xml">x</a><a href="https://other.example.com/google.xml">bad</a>', "https://example.test")
    assert found == ("https://example.test/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",)

def test_rss_title_link_are_accepted_with_google_id_price():
    body = b'''<?xml version="1.0"?><rss xmlns:g="http://base.google.com/ns/1.0"><channel><item><g:id>SKU</g:id><title>Widget</title><link>https://example.test/p/1</link><g:description>x</g:description><g:price>1999 INR</g:price><g:availability>in stock</g:availability></item></channel></rss>'''
    result = validate_xml(body, "application/xml")
    assert result.valid is True
    assert result.product_items == 1

def test_full_google_gpf_is_preferred_to_partial():
    full = "https://onlyssd.com/?woocommerce_gpf=google"
    partial = "https://onlyssd.com/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100"
    assert feed_priority(full) < feed_priority(partial)

def test_netscape_cookie_header_parser(tmp_path: Path):
    jar = tmp_path / "cookies.txt"
    jar.write_text(
        "# Netscape HTTP Cookie File\n"
        ".example.test\tTRUE\t/\tFALSE\t0\tPHPSESSID\tabc123\n"
        ".example.test\tTRUE\t/\tFALSE\t0\twoocommerce_session\tdef456\n",
        encoding="utf-8",
    )
    assert _cookie_header_from_netscape(str(jar)) == "PHPSESSID=abc123; woocommerce_session=def456"

def test_ctxfeed_generated_filename_candidates():
    body = '{"feeds":[{"feed_name":"aB12-google","file_name":"ignored.xml"}],"name":"site-feed"}'
    found = ctxfeed_urls(body, "https://example.test")
    assert "https://example.test/?woo_feed=aB12-google&wt=xml" in found
    assert "https://example.test/wp-content/uploads/woo-feed/google/xml/aB12-google.xml" in found

def test_public_json_parser_accepts_cdx_array():
    result = _public_json_lines(
        [sys.executable, "-c", 'import json; print(json.dumps([["timestamp","original","statuscode"],["20260927","https://example.test/feed.xml","200"]]))'],
        timeout_s=5.0,
    )
    assert result == [{
        "timestamp": "20260927",
        "original": "https://example.test/feed.xml",
        "statuscode": "200",
    }]

def test_explicit_external_feed_url_is_discovered():
    body = '<script>window.feedConfig = {"feed_url":"https://feeds.example-cdn.test/store/google.xml"};</script>'
    found = extract_explicit_feed_urls(body, "https://shop.example.test")
    assert found == ("https://feeds.example-cdn.test/store/google.xml",)

def test_external_non_feed_link_is_not_discovered():
    body = '<a href="https://other.example.test/products.xml">external</a>'
    assert extract_explicit_feed_urls(body, "https://shop.example.test") == ()

def test_learned_feed_patterns_preserve_verified_path_and_query(tmp_path: Path):
    shard = tmp_path / "prior"
    shard.mkdir()
    (shard / "site.json").write_text(
        '{"site":"Only SDD","root":"https://onlyssd.com","native_feed_url":"https://onlyssd.com/?woocommerce_gpf=google","evidence":{"records":[{"requested_url":"https://onlyssd.com/legacy.xml","validation":{"valid":true}}]}}',
        encoding="utf-8",
    )
    found = load_learned_feed_patterns((tmp_path,))
    assert "/?woocommerce_gpf=google" in found
    assert "/legacy.xml" in found

def test_explicit_external_candidates_reach_validation_group():
    discovered = {
        "https://shop.example.test/google.xml",
        "https://feeds.example-cdn.test/store/google.xml",
    }
    same_site, external = validation_candidate_groups(
        discovered,
        {"https://feeds.example-cdn.test/store/google.xml"},
        "https://shop.example.test",
    )
    assert same_site == ["https://shop.example.test/google.xml"]
    assert external == ["https://feeds.example-cdn.test/store/google.xml"]

def test_generated_upload_filename_sweep_contains_known_variants():
    urls = generated_upload_feed_candidates("https://example.test", "KRG KART")
    assert "https://example.test/wp-content/uploads/google.xml" in urls
    assert "https://example.test/wp-content/uploads/google-feed.xml" in urls
    assert "https://example.test/wp-content/uploads/woo-feed/google/xml/google-shopping.xml" in urls
    assert "https://example.test/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml" in urls
    assert "https://example.test/wp-content/uploads/woo-feed/google/xml/google-shopping.xml.gz" in urls
    assert len(urls) >= 500

def test_wordpress_media_feed_candidate_discovery():
    body = '[{"source_url":"https://shop.example.test/wp-content/uploads/google-feed.xml","guid":{"rendered":"https://shop.example.test/wp-content/uploads/google-feed.xml"}}]'
    found = wp_media_feed_candidates(body, "https://shop.example.test")
    assert found == ("https://shop.example.test/wp-content/uploads/google-feed.xml",)
