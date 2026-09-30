import sys
import types
from pathlib import Path
import importlib.util

sys.modules.setdefault("httpx", types.ModuleType("httpx"))

path = Path(__file__).resolve().parents[1] / "tools" / "woocommerce_feed_guess_v2.py"
spec = importlib.util.spec_from_file_location("wc_guess_v2", path)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def test_new_documented_family_fingerprints():
    hits = module.BASE.find_plugin_hits(
        ["/wp-content/plugins/best-woocommerce-feed/"],
        ["best-woocommerce-feed"],
        [],
    )
    assert "rexfed_product_feed" in hits

    hits = module.BASE.find_plugin_hits(
        ["product-xml-feeds-for-woocommerce"],
        ["product-xml-feeds-for-woocommerce"],
        [],
    )
    assert "wpfactory_product_xml_feeds" in hits

    hits = module.BASE.find_plugin_hits(["/apfw-feed/abc.xml"], [], [])
    assert "svmpforge_product_feed" in hits

def test_static_assets_are_removed():
    root = "https://example.com"
    urls = [
        root + "/wp-content/plugins/x/google.js?woocommerce_gpf=google",
        root + "/wp-content/themes/x/google-feed.css",
        root + "/wp-content/uploads/google.xml",
    ]
    kept = module.filter_explicit_feed_candidates(urls)
    assert root + "/wp-content/uploads/google.xml" in kept
    assert all(not u.endswith((".js", ".css")) for u in kept)

def test_query_discovery_does_not_promote_plugin_js():
    root = "https://example.com"
    blob = '<script src="/wp-content/plugins/x/google.js?woocommerce_gpf=google"></script> <a href="/?woocommerce_gpf=google">feed</a>'
    found = module.query_feed_candidates(blob, root)
    assert root + "/?woocommerce_gpf=google" in found
    assert all("/plugins/x/google.js" not in u for u in found)

def test_native_validator_requires_complete_item():
    split = b'''<rss xmlns:g="http://base.google.com/ns/1.0"><channel>
    <item><g:id>1</g:id><g:title>A</g:title></item>
    <item><g:link>https://example.com/a</g:link><g:price>1 INR</g:price></item>
    </channel></rss>'''
    assert not module.native_google_valid(split, "application/xml")[0]

    complete = b'''<rss xmlns:g="http://base.google.com/ns/1.0"><channel>
    <item><g:id>1</g:id><g:title>A</g:title><g:link>https://example.com/a</g:link><g:price>1 INR</g:price></item>
    </channel></rss>'''
    ok, count, digest = module.native_google_valid(complete, "application/xml")
    assert ok and count == 1 and digest

def test_documented_wpfactory_probe_is_present():
    assert module.BASE.PLUGIN_CANDIDATES["wpfactory_product_xml_feeds"] == ["/products.xml"]
