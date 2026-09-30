import sys
import types
from pathlib import Path
import importlib.util

sys.modules.setdefault("httpx", types.ModuleType("httpx"))
MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "woocommerce_v175_plugin_fingerprint_22.py"
spec = importlib.util.spec_from_file_location("wc_v175_internal_discovery", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_internal_page_discovery_prefers_store_product_pages():
    root = "https://example.com"
    html = '''
      <a href="/">Home</a>
      <a href="/about/">About</a>
      <a href="/shop/">Shop</a>
      <a href="/product/gpu-1/">GPU</a>
      <a href="/product/gpu-2/">GPU 2</a>
      <a href="/cart/">Cart</a>
    '''
    found = module.discover_internal_page_urls(html, root, 2)
    assert root + "/product/gpu-1/" in found
    assert root + "/shop/" in found or root + "/product/gpu-2/" in found
    assert all("/cart/" not in u for u in found)
