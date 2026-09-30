from pathlib import Path
import importlib.util
import sys


MODULE_PATH = Path(__file__).resolve().parent / "woocommerce_v175_plugin_fingerprint_22.py"
spec = importlib.util.spec_from_file_location("woocommerce_v175_feed_detection", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_escaped_wc_gla_namespace_is_normalized_and_detected():
    namespaces = module.parse_namespaces('{"namespaces":["wc\\/gla"]}')
    assert "wc/gla" in namespaces
    hits = module.find_plugin_hits([], [], namespaces)
    assert hits["google_for_woocommerce"] == ["wc/gla"]


def test_sitemap_xml_is_not_explicit_google_feed_evidence():
    text = (
        '<loc>https://aulaindia.com/sitemap_index.xml</loc>'
        '<loc>https://aulaindia.com/wp-content/uploads/google.xml</loc>'
    )
    explicit = module.explicit_xml_candidates(text, "https://aulaindia.com")
    feed_candidates = module.filter_explicit_feed_candidates(explicit)
    assert "https://aulaindia.com/sitemap_index.xml" in explicit
    assert "https://aulaindia.com/sitemap_index.xml" not in feed_candidates
    assert "https://aulaindia.com/wp-content/uploads/google.xml" in feed_candidates