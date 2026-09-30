import sys
import types
from pathlib import Path
import importlib.util

# The generic repository test environment does not install extractor-only httpx.
sys.modules.setdefault("httpx", types.ModuleType("httpx"))

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "woocommerce_v175_plugin_fingerprint_22.py"
spec = importlib.util.spec_from_file_location("wc_v175_feed_detection", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_escaped_gla_namespace_is_detected():
    blob = r'{"namespaces":["wc\/gla","wc\/store/v1"]}'
    ns = module.parse_namespaces(blob)
    hits = module.find_plugin_hits([blob], [], ns)
    assert "wc/gla" in ns
    assert "google_for_woocommerce" in hits


def test_sitemap_is_not_explicit_feed():
    root = "https://example.com"
    urls = [
        root + "/sitemap_index.xml",
        root + "/wp-sitemap.xml",
        root + "/robots.txt",
        root + "/wp-content/uploads/google.xml",
    ]
    kept = module.filter_explicit_feed_candidates(urls)
    assert root + "/wp-content/uploads/google.xml" in kept
    assert all("sitemap" not in u and not u.endswith("robots.txt") for u in kept)
