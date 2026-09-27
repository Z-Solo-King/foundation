#!/usr/bin/env python3
"""Fast, native-only WooCommerce Google Merchant XML URL hunt."""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import ipaddress
import html
import json
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
GOOGLE_NS = "http://base.google.com/ns/1.0"
BLOCK_MARKERS = ("just a moment", "cf-chl-", "cf-turnstile", "captcha", "access denied", "attention required", "checking your browser")
ITEM_TAGS = {"item", "entry"}
SITEMAP_ROOTS = {"urlset", "sitemapindex"}

TARGETS = (
    ("Aarna Computers", "https://aarnacomputers.com"),
    ("Ads Store", "https://adsstore.in"),
    ("avikaretails", "https://avikaretails.com"),
    ("EZPZ Solutions", "https://www.ezpzsolutions.in"),
    ("GamesNComps", "https://gamesncomps.com"),
    ("Geekbees", "https://geekbees.in"),
    ("hotshiftpc", "https://hotshiftpc.com"),
    ("itgadgetsonline", "https://itgadgetsonline.com"),
    ("ithunt", "https://ithunt.in"),
    ("KC Computers", "https://kccomputers.co.in"),
    ("KRG KART", "https://krgkart.com"),
    ("Kryptronix Gaming", "https://kryptronix.in"),
    ("NCL Computer", "https://nclcomputer.com"),
    ("networkitstore", "https://networkitstore.in"),
    ("nexusinfosys", "https://www.mynexusinfosys.com"),
    ("Only SDD", "https://onlyssd.com"),
    ("PC Kumar Infotech", "https://pckumar.in"),
    ("PC Studio", "https://www.pcstudio.in"),
    ("PCHubShop", "https://www.pchubshop.com"),
    ("Prime ABGB", "https://www.primeabgb.com"),
    ("quickincomputers", "https://quickincomputers.com"),
    ("SCL Gaming", "https://sclgaming.in"),
    ("solankienterprises", "https://solankienterprises.com"),
    ("Variety Infotech", "https://varietyinfotech.com"),
    ("Viper PC", "https://viperpc.in"),
    ("AULA India", "https://aulaindia.com"),
    ("Cosmic Byte", "https://www.thecosmicbyte.com"),
    ("Meckeys", "https://www.meckeys.com"),
    ("Moskeys", "https://moskeys.com"),
    ("Ninja Dog", "https://ninjadog.in"),
    ("StacksKB", "https://stackskb.com"),
    ("Theproaudio", "https://www.theproaudio.com"),
)

FAST_PATHS = (
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=25",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=50",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
    "/?woocommerce_gpf=google&gpf_start=1&gpf_limit=100",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=25",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=50",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=500",
    "/feed/google","/feed/products","/products/feed","/store/feed",
    "/?feed=google","/?feed=merchant","/?feed=google-products","/?feed=google_shopping",
    "/?feed=google_base","/?feed=google-feed","/?format=google","/?format=xml&feed=google",
    "/gpf-feed.xml","/gpf_google.xml","/gpf_google_feed.xml","/google-base.xml","/google/base.xml",
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/google.xml", "/google_feed.xml", "/google-feed.xml",
    "/google-products.xml", "/google-product-feed.xml",
    "/google-shopping.xml", "/google-shopping-feed.xml",
    "/google-merchant.xml", "/google-merchant-feed.xml",
    "/merchant.xml", "/merchant-feed.xml", "/product-feed.xml",
    "/feed/google.xml", "/feeds/google.xml",
)

SLOW_GPF_PATHS = (
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=2500",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=5000",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=2500",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=5000",
)

MEDIUM_PATHS = (
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/google",
    "/wp-json/feed-products/v1/google.xml",
    "/wp-json/google-product-feed/v1/xml",
    "/wp-json/google-feed/v1/xml",
    "/wp-json/woo-feed/v1/google.xml",
    "/wp-content/uploads/woo-feed/google.xml",
    "/wp-content/uploads/woo-feed/google-feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/google-shopping-products.xml", "/google-shopping-products-feed.xml",
    "/google_product_feed.xml", "/googlefeed.xml", "/google-products-feed.xml",
    "/merchant_feed.xml", "/products/feed.xml", "/products_feed.xml",
    "/product_feed.xml", "/productfeed.xml", "/feed-products.xml", "/feed_products.xml",
    "/catalog/google_feed.xml", "/media/google.xml", "/media/feed/google_base.xml",
    "/wp-content/uploads/woo-feed/google/google.xml",
    "/wp-content/uploads/woo-feed/google/google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/feeds/google-product-feed.xml", "/feeds/google-products.xml", "/feeds/google-shopping-feed.xml",
    "/feed/google-feed.xml", "/feed/google-products.xml", "/feed/google-product-feed.xml",
    "/feed/google-shopping.xml", "/feed/google-shopping-feed.xml",
)

DIRECTORIES = (
    "/wp-content/uploads/woo-feed/google/xml/",
    "/wp-content/uploads/woo-feed/google/",
    "/wp-content/uploads/woo-feed/",
    "/wp-content/uploads/woo-product-feed-pro/xml/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/codesolz-feeds/",
    "/feeds/", "/feed/",
)

DISCOVERY_PATHS = ("/", "/robots.txt", "/sitemap.xml", "/sitemap.rss", "/sitemap_index.xml", "/wp-sitemap.xml", "/wp-json/", "/feed/")

CTXFEED_PATHS = tuple(f"/wp-json/ctxfeed/{v}/feeds" for v in ("v8","v7","v6","v5","v4","v3","v2","v1"))

PLUGIN_FINGERPRINT_PATHS = (
    ("adtribes", "/wp-content/plugins/woo-product-feed-pro/readme.txt"),
    ("ctxfeed", "/wp-content/plugins/webappick-product-feed-for-woocommerce/readme.txt"),
    ("wpmr", "/wp-content/plugins/wp-product-feed-manager/readme.txt"),
)

# Known public WooCommerce feed filename grammar.  Includes exact names observed in
# published plugin documentation/examples plus common separator/semantic variants.
UPLOAD_FEED_STEMS = (
    "google", "google-feed", "google_feed", "googlefeed",
    "google-xml", "google_xml", "google-base", "google_base", "googlebase",
    "google-merchant", "google_merchant", "google-merchant-feed", "google_merchant_feed",
    "google-product", "google_product", "google-products", "google_products",
    "google-product-feed", "google_product_feed", "google-shopping", "google_shopping",
    "google-shopping-feed", "google_shopping_feed",
    "google-shopping-products", "google_shopping_products",
    "merchant", "merchant-feed", "merchant_feed", "merchant-xml", "merchant_xml",
    "merchant-google", "merchant_google", "merchant-google-feed", "merchant_google_feed",
    "shopping", "shopping-feed", "shopping_feed", "shopping-xml", "shopping_xml",
    "shopping-google", "shopping_google", "shopping-google-feed", "shopping_google_feed",
    "product", "product-feed", "product_feed", "product-xml", "product_xml",
    "products", "products-feed", "products_feed", "products-xml", "products_xml",
    "feed", "feed-google", "feed_google", "feed-merchant", "feed_merchant",
    "feed-xml", "feed_xml", "feed-products", "feed_products",
    "google-shopping-xml", "google_shopping_xml",
    "merchant-google-xml", "merchant_google_xml",
    "gpf", "gpf-feed", "gpf_feed", "gpf-google", "gpf_google",
)

UPLOAD_FEED_DIRECTORIES = (
    "/wp-content/uploads/",
    "/wp-content/uploads/woo-feed/",
    "/wp-content/uploads/woo-feed/google/",
    "/wp-content/uploads/woo-feed/google/xml/",
    "/wp-content/uploads/woo-feed/xml/",
    "/wp-content/uploads/woo-product-feed-pro/xml/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/codesolz-feeds/",
    "/wp-content/uploads/google/",
    "/wp-content/uploads/merchant/",
    "/wp-content/uploads/feeds/",
    "/wp-content/uploads/rex-feed/",
    "/wp-content/uploads/product-feed/",
    "/wp-content/uploads/google-feed/",
    "/wp-content/uploads/merchant-feed/",
)

FILENAME_SEMANTIC_GROUPS = (
    ("google", "merchant", "shopping", "gmc"),
    ("feed", "feeds", "product", "products", "catalog"),
    ("base", "xml", "data", "export", "listing"),
)
FILENAME_SEPARATORS = ("-", "_", "")
FILENAME_SUFFIX_WORDS = (
    "google-feed-xml", "google_feed_xml", "googlefeedxml",
    "google-shopping-feed", "google_shopping_feed", "googleshoppingfeed",
    "google-product-feed", "google_product_feed", "googleproductfeed",
    "google-products-feed", "google_products_feed", "googleproductsfeed",
    "google-merchant-feed", "google_merchant_feed", "googlemerchantfeed",
    "google-shopping-products", "google_shopping_products", "googleshoppingproducts",
    "merchant-google-feed", "merchant_google_feed", "merchantgooglefeed",
    "shopping-google-feed", "shopping_google_feed", "shoppinggooglefeed",
    "product-google-feed", "product_google_feed", "productgooglefeed",
    "products-google-feed", "products_google_feed", "productsgooglefeed",
    "feed-google-products", "feed_google_products", "feedgoogleproducts",
    "feed-google-shopping", "feed_google_shopping", "feedgoogleshopping",
    "feed-merchant-google", "feed_merchant_google", "feedmerchantgoogle",
    "feed-product-google", "feed_product_google", "feedproductgoogle",
    "merchant-center-feed", "merchant_center_feed", "merchantcenterfeed",
    "merchant-centre-feed", "merchant_centre_feed", "merchantcentrefeed",
    "google-merchant-center", "google_merchant_center", "googlemerchantcenter",
    "google-merchant-centre", "google_merchant_centre", "googlemerchantcentre",
    "product-data", "product_data", "productdata",
    "products-data", "products_data", "productsdata",
    "google-product-data", "google_product_data", "googleproductdata",
    "merchant-product-data", "merchant_product_data", "merchantproductdata",
)

def _semantic_feed_stems() -> tuple[str, ...]:
    stems: set[str] = set(FILENAME_SUFFIX_WORDS)
    for g1 in FILENAME_SEMANTIC_GROUPS:
        for g2 in FILENAME_SEMANTIC_GROUPS:
            if g1 is g2:
                continue
            for a in g1:
                for b in g2:
                    for sep in FILENAME_SEPARATORS:
                        stems.add(f"{a}{sep}{b}")
    # Three-part combinations in every order of semantic roles.
    import itertools
    for perm in itertools.permutations(range(len(FILENAME_SEMANTIC_GROUPS))):
        for a in FILENAME_SEMANTIC_GROUPS[perm[0]]:
            for b in FILENAME_SEMANTIC_GROUPS[perm[1]]:
                for d in FILENAME_SEMANTIC_GROUPS[perm[2]]:
                    for sep in FILENAME_SEPARATORS[:2]:
                        stems.add(f"{a}{sep}{b}{sep}{d}")
    return tuple(sorted(stems, key=lambda x: (0 if "google" in x else 1, len(x), x)))

SEMANTIC_FEED_STEMS = _semantic_feed_stems()

def generated_upload_feed_candidates(root: str, site: str) -> tuple[str, ...]:
    """Generate deterministic upload-feed and named-feed candidates."""
    slug = re.sub(r"[^a-z0-9]+", "-", site.lower()).strip("-")
    site_forms = list(dict.fromkeys(x for x in (
        slug,
        slug.replace("-", "_"),
        slug.replace("-", ""),
    ) if x))

    site_stems: list[str] = []
    for s in site_forms:
        for stem in SEMANTIC_FEED_STEMS[:220]:
            for sep in FILENAME_SEPARATORS:
                site_stems.extend((
                    f"{s}{sep}{stem}",
                    f"{stem}{sep}{s}",
                ))
        # Explicit CTXFeed-style concatenated names observed in public examples.
        for suffix in ("google", "googleshopping", "googlefeed", "googleproductfeed",
                       "googleproducts", "googleshoppingfeed", "merchantfeed",
                       "googlemerchantfeed", "productfeed"):
            site_stems.extend((f"{s}{suffix}", f"{suffix}{s}"))

    stems = list(dict.fromkeys([*UPLOAD_FEED_STEMS, *SEMANTIC_FEED_STEMS, *site_stems]))
    urls: set[str] = set()
    for directory in UPLOAD_FEED_DIRECTORIES:
        for stem in stems[:420]:
            for extension in (".xml", ".xml.gz"):
                path = directory.rstrip("/") + "/" + stem + extension
                urls.add(urllib.parse.urljoin(root.rstrip("/") + "/", path.lstrip("/")))
    # CTXFeed exposes named feeds as /?feed=<feed-name>; these are first-class
    # native candidates, not reconstructed data.
    for stem in stems[:420]:
        urls.add(urllib.parse.urljoin(root.rstrip("/") + "/", "?feed=" + urllib.parse.quote(stem)))
    # Site-scoped common named-feed aliases.
    for s in site_forms:
        for stem in ("google", "google-shopping", "google-feed", "google-products", "merchant-feed"):
            for sep in FILENAME_SEPARATORS:
                name = f"{s}{sep}{stem}"
                urls.add(urllib.parse.urljoin(root.rstrip("/") + "/", "?feed=" + urllib.parse.quote(name)))
    return tuple(sorted(urls, key=lambda u: (feed_priority(u), len(u), u)))


def rex_numeric_candidates(root: str, known_urls: set[str]) -> tuple[str, ...]:
    """Probe bounded numeric RexFeed IDs only when an ID family was observed."""
    ids: set[int] = set()
    for u in known_urls:
        m = re.search(r"/rex-feed/feed-(\d+)\.xml(?:\.gz)?$", u, re.I)
        if m:
            ids.add(int(m.group(1)))
    candidates: set[str] = set()
    for base_id in ids:
        lo, hi = max(1, base_id - 25), base_id + 25
        for i in range(lo, hi + 1):
            candidates.add(urllib.parse.urljoin(root.rstrip("/") + "/", f"/wp-content/uploads/rex-feed/feed-{i}.xml"))
    return tuple(sorted(candidates, key=lambda u: (feed_priority(u), u)))


@dataclass(frozen=True)
class Fetch:
    requested_url: str
    final_url: str
    status: int
    content_type: str
    body: bytes
    elapsed_ms: int
    error: str | None = None

@dataclass(frozen=True)
class Validation:
    valid: bool
    format: str
    product_items: int
    google_fields: int
    reasons: tuple[str, ...]
    sha256: str = ""

@dataclass(frozen=True)
class SiteResult:
    site: str
    root: str
    status: str
    native_feed_url: str | None
    evidence: dict[str, object]
    elapsed_s: float


def same_host(a: str, b: str) -> bool:
    ah = (urllib.parse.urlsplit(a).hostname or "").lower().removeprefix("www.")
    bh = (urllib.parse.urlsplit(b).hostname or "").lower().removeprefix("www.")
    return bool(ah and bh and ah == bh)


def absolute(root: str, raw: str) -> str | None:
    raw = html.unescape(str(raw or "")).strip().rstrip(".,);")
    if not raw:
        return None
    try:
        url = urllib.parse.urljoin(root.rstrip("/") + "/", raw)
        return url if url.startswith(("http://", "https://")) and same_host(url, root) else None
    except ValueError:
        return None


def _cookie_header_from_netscape(path: str) -> str:
    parts: list[str] = []
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.startswith("#") or "\t" not in line:
                continue
            cols = line.split("\t")
            if len(cols) >= 7 and cols[6]:
                parts.append(f"{cols[5]}={cols[6]}")
    except OSError:
        return ""
    return "; ".join(dict.fromkeys(parts))


def warm_site_session(root: str, timeout: float = 20.0) -> str:
    """Establish a normal same-site HTTP session and return its cookies."""
    meta_path = body_path = jar_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="session-meta-", delete=False) as meta_fp, tempfile.NamedTemporaryFile(prefix="session-body-", delete=False) as body_fp, tempfile.NamedTemporaryFile(prefix="session-cookie-", delete=False) as jar_fp:
            meta_path, body_path, jar_path = meta_fp.name, body_fp.name, jar_fp.name
        cmd = [
            "curl", "--silent", "--show-error", "--location", "--compressed",
            "--connect-timeout", "12", "--max-time", str(int(max(5.0, timeout))),
            "-A", UA,
            "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.1",
            "-H", "Accept-Language: en-IN,en;q=0.9",
            "-c", jar_path, "-o", body_path,
            "-w", "%{http_code}\n",
            root.rstrip("/") + "/",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=max(15.0, timeout + 8), check=False)
        body = Path(body_path).read_text(encoding="utf-8", errors="replace")
        lines = (proc.stdout or "").splitlines()
        status = int(lines[0]) if lines and lines[0].isdigit() else 0
        if status != 200 or any(marker in body[:16000].lower() for marker in BLOCK_MARKERS):
            return ""
        return _cookie_header_from_netscape(jar_path)
    except (subprocess.TimeoutExpired, OSError, ValueError):
        return ""
    finally:
        for path in (meta_path, body_path, jar_path):
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass


def _historical_url_filter(url: str, root: str) -> bool:
    """Keep only same-site historical URLs that could plausibly be Merchant feeds."""
    u = absolute(root, url)
    if not u:
        return False
    return bool(
        re.search(r"\.xml(?:\.gz)?(?:[?#].*)?$", u, re.I)
        or re.search(r"(feed|merchant|shopping|woocommerce_gpf|google|woo[-_]?feed|wppfm)", u, re.I)
    )


def _public_json_lines(command: list[str], timeout_s: float = 25.0) -> list[dict[str, object]]:
    try:
        proc = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=max(10.0, timeout_s + 5.0),
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError):
        return []

    text_out = (proc.stdout or "").strip()
    if not text_out:
        return []

    # Support both JSON Lines (Common Crawl) and JSON-array CDX responses
    # (Wayback).  CDX JSON arrays may have the first row as column headers.
    try:
        parsed = json.loads(text_out)
    except json.JSONDecodeError:
        parsed = None

    if isinstance(parsed, dict):
        return [parsed]
    if isinstance(parsed, list):
        if parsed and all(isinstance(item, dict) for item in parsed):
            return [item for item in parsed if isinstance(item, dict)]
        if parsed and isinstance(parsed[0], list):
            header = [str(x) for x in parsed[0]]
            records: list[dict[str, object]] = []
            for row in parsed[1:]:
                if isinstance(row, list):
                    records.append({
                        header[i]: row[i] if i < len(row) else ""
                        for i in range(len(header))
                    })
            return records

    out: list[dict[str, object]] = []
    for line in text_out.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def plugin_fingerprint(root: str, cookie_header: str) -> tuple[str, ...]:
    found: list[str] = []
    for name, path in PLUGIN_FINGERPRINT_PATHS:
        result = fetch(urllib.parse.urljoin(root.rstrip("/") + "/", path.lstrip("/")), 8.0, cookie_header, root)
        if result.status != 200 or not result.body:
            continue
        sample = result.body[:12000].decode("utf-8", "replace").lower()
        if name == "adtribes" and "product feed" in sample and "adtribes" in sample:
            found.append("adtribes")
        elif name == "ctxfeed" and "ctx feed" in sample:
            found.append("ctxfeed")
        elif name == "wpmr" and ("product feed" in sample or "wpmr" in sample):
            found.append("wpmr")
    return tuple(sorted(set(found)))


def historical_feed_discover(root: str, timeout_s: float = 25.0) -> tuple[str, ...]:
    """Discover historical feed URLs from public Common Crawl and Wayback indexes.
    Historical URLs are candidates only; every candidate still needs a current
    live fetch and native Google Merchant XML validation.
    """
    host = urllib.parse.urlsplit(root).hostname or ""
    host = host.lower().removeprefix("www.")
    if not host:
        return ()

    found: set[str] = set()

    # Common Crawl: choose the three newest published indexes so an endpoint
    # that existed recently still has a chance of being recovered.
    try:
        cc_cmd = [
            "curl", "--silent", "--show-error", "--location",
            "--connect-timeout", "8", "--max-time", str(int(timeout_s)),
            "-A", UA, "https://index.commoncrawl.org/collinfo.json",
        ]
        cc_info_proc = subprocess.run(
            cc_cmd, capture_output=True, text=True,
            timeout=max(12.0, timeout_s + 5.0), check=False
        )
        cc_info = json.loads(cc_info_proc.stdout or "[]")
        indexes = [
            str(x.get("id") or "")
            for x in (cc_info if isinstance(cc_info, list) else [])
            if isinstance(x, dict) and str(x.get("id") or "").startswith("CC-MAIN-")
        ][:3]
    except (subprocess.TimeoutExpired, OSError, ValueError, json.JSONDecodeError):
        indexes = []

    for idx in indexes:
        params = urllib.parse.urlencode({
            "url": f"{host}/*",
            "output": "json",
            "filter": "status:200",
            "pageSize": "200",
        })
        api = f"https://index.commoncrawl.org/{idx}-index?{params}"
        rows = _public_json_lines([
            "curl", "--silent", "--show-error", "--location",
            "--connect-timeout", "8", "--max-time", str(int(timeout_s)),
            "-A", UA, api,
        ], timeout_s)
        for row in rows:
            for key in ("url", "original"):
                raw = str(row.get(key) or "")
                if raw and _historical_url_filter(raw, root):
                    u = absolute(root, raw)
                    if u:
                        found.add(u)
            if len(found) >= 200:
                break
        if len(found) >= 200:
            break

    # Wayback CDX provides another public historical URL index and often
    # contains generated feed paths missing from current HTML.
    params = urllib.parse.urlencode({
        "url": f"{host}/*",
        "output": "json",
        "fl": "timestamp,original,mimetype,statuscode",
        "filter": "statuscode:200",
        "collapse": "urlkey",
        "limit": "300",
    })
    wayback_api = f"https://web.archive.org/cdx/search/cdx?{params}"
    rows = _public_json_lines([
        "curl", "--silent", "--show-error", "--location",
        "--connect-timeout", "8", "--max-time", str(int(timeout_s)),
        "-A", UA, wayback_api,
    ], timeout_s)
    for row in rows:
        raw = str(row.get("original") or "")
        if raw and _historical_url_filter(raw, root):
            u = absolute(root, raw)
            if u:
                found.add(u)
    return tuple(sorted(found)[:300])


def browser_session_discover(
    root: str,
    timeout_s: float = 50.0,
    candidate_urls: tuple[str, ...] = (),
) -> tuple[str, tuple[str, ...], dict[str, object]]:
    """Use one normal browser context to discover and probe public feed endpoints."""
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return "", (), {"available": False}

    started = time.monotonic()
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    locale="en-IN",
                    user_agent=UA,
                    viewport={"width": 1366, "height": 768},
                )
                page = context.new_page()
                observed_requests: set[str] = set()
                observed_response_urls: set[str] = set()
                browser_validated_urls: set[str] = set()
                visited_pages: set[str] = set()
                homepage_links: list[str] = []

                def observe_request(request):
                    u = str(getattr(request, "url", "") or "")
                    if u and re.search(r"(?:\.xml(?:\.gz)?(?:[?#].*)?|feed|merchant|shopping|woocommerce_gpf|google)", u, re.I):
                        observed_requests.add(u)

                def observe_response(response):
                    u = str(getattr(response, "url", "") or "")
                    if not u or not u.startswith(("http://", "https://")):
                        return
                    try:
                        headers = {str(k).lower(): str(v).lower() for k, v in response.all_headers().items()}
                        ct = headers.get("content-type", "")
                        looks_feed = (
                            "xml" in ct or "rss" in ct or "atom" in ct
                            or re.search(r"(?:\.xml(?:\.gz)?(?:[?#].*)?|feed|merchant|shopping|woocommerce_gpf|google)", u, re.I)
                        )
                        if not looks_feed:
                            return
                        body = response.body()
                        if len(body) <= 25 * 1024 * 1024 and validate_xml(body, ct).valid:
                            observed_response_urls.add(u)
                    except Exception:
                        return

                page.on("request", observe_request)
                page.on("response", observe_response)

                page.goto(root.rstrip("/") + "/", wait_until="domcontentloaded", timeout=int(timeout_s * 1000))
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass

                homepage_html = page.content()
                challenge_seen = any(marker in homepage_html[:20000].lower() for marker in BLOCK_MARKERS)
                try:
                    homepage_links = page.locator("a[href]").evaluate_all(
                        "(els) => els.map(e => e.href).filter(Boolean)"
                    )
                except Exception:
                    homepage_links = []

                # Probe public discovery routes in this browser context.
                for path in ("/robots.txt", "/sitemap.xml", "/sitemap.rss", "/sitemap_index.xml", "/wp-sitemap.xml", "/feed/"):
                    try:
                        page.goto(
                            urllib.parse.urljoin(root.rstrip("/") + "/", path.lstrip("/")),
                            wait_until="domcontentloaded",
                            timeout=7000,
                        )
                    except Exception:
                        continue
                    try:
                        page.wait_for_load_state("networkidle", timeout=1800)
                    except Exception:
                        pass
                    try:
                        route_body = page.content()
                        if len(route_body) <= 20 * 1024 * 1024:
                            observed_requests.update(extract_urls(route_body, root))
                            observed_response_urls.update(extract_explicit_feed_urls(route_body, root))
                    except Exception:
                        pass

                # IMPORTANT: use the browser's own API context to request the
                # candidate feed URLs. BrowserContext.request shares cookies with
                # the browser context, so sites that treat curl and a real browser
                # differently get a proper session-aware probe.
                request_candidates = []
                for raw in candidate_urls:
                    u = _explicit_http_url(root, raw)
                    if not u:
                        continue
                    if same_host(u, root) or u in extract_explicit_feed_urls(homepage_html, root):
                        request_candidates.append(u)
                request_candidates = list(dict.fromkeys(request_candidates))[:80]

                api_request = context.request
                for u in request_candidates:
                    try:
                        resp = api_request.get(
                            u,
                            timeout=12000,
                            headers={
                                "Referer": root.rstrip("/") + "/",
                                "Accept": "application/xml, application/rss+xml, text/xml, */*",
                                "Accept-Language": "en-IN,en;q=0.9",
                            },
                            fail_on_status_code=False,
                        )
                        body = resp.body()
                        ct = str(resp.headers.get("content-type", ""))
                        validation = validate_xml(body, ct) if resp.status == 200 else Validation(False, "not_checked", 0, 0, ())
                        if validation.valid:
                            browser_validated_urls.add(u)
                        elif resp.status == 200:
                            # A response that is XML-looking/feed-like is still useful
                            # as discovery evidence, but not as a verified URL.
                            observed_requests.add(u)
                    except Exception:
                        continue

                # Crawl a bounded sample of public product/store pages, using the same
                # browser context, to expose feed configuration and XHR endpoints.
                if not challenge_seen:
                    page_candidates = []
                    for href in homepage_links:
                        u = _explicit_http_url(root, str(href))
                        if not u or not same_host(u, root):
                            continue
                        path_l = urllib.parse.urlsplit(u).path.lower()
                        if any(token in path_l for token in ("/product/", "/products/", "/shop/", "/item/", "/category/", "/product-category/")):
                            page_candidates.append(u)
                        if len(page_candidates) >= 12:
                            break

                    for u in page_candidates:
                        if u in visited_pages:
                            continue
                        visited_pages.add(u)
                        try:
                            page.goto(u, wait_until="domcontentloaded", timeout=9000)
                        except Exception:
                            continue
                        try:
                            page.wait_for_load_state("networkidle", timeout=2500)
                        except Exception:
                            pass
                        try:
                            html_body = page.content()
                            observed_requests.update(extract_urls(html_body, root))
                            explicit = extract_explicit_feed_urls(html_body, root)
                            observed_requests.update(explicit)
                        except Exception:
                            pass

                body = page.content()
                candidates = set(extract_urls(homepage_html, root))
                candidates.update(extract_explicit_feed_urls(homepage_html, root))
                candidates.update(extract_urls(body, root))
                candidates.update(extract_explicit_feed_urls(body, root))
                candidates.update(observed_requests)
                candidates.update(observed_response_urls)
                candidates.update(browser_validated_urls)

                for href in page.locator("a[href], link[href]").evaluate_all(
                    "(els) => els.map(e => e.href).filter(Boolean)"
                ):
                    u = _explicit_http_url(root, str(href))
                    if u and (
                        re.search(r"\.xml(?:\.gz)?(?:[?#].*)?$", u, re.I)
                        or re.search(r"(feed|merchant|shopping|woocommerce_gpf|google)", u, re.I)
                    ):
                        candidates.add(u)

                cookies = context.cookies()
                pairs = [f"{c['name']}={c['value']}" for c in cookies if c.get("name") and c.get("value")]
                return "; ".join(dict.fromkeys(pairs)), tuple(sorted(candidates)), {
                    "available": True,
                    "status": "ok",
                    "elapsed_ms": int((time.monotonic() - started) * 1000),
                    "cookie_count": len(pairs),
                    "candidate_count": len(candidates),
                    "browser_validated_feed_count": len(browser_validated_urls),
                    "response_feed_count": len(observed_response_urls),
                    "visited_public_pages": len(visited_pages),
                    "challenge_seen": challenge_seen,
                }
            finally:
                browser.close()
    except Exception as exc:
        return "", (), {
            "available": True,
            "status": "browser_error",
            "error": type(exc).__name__,
            "elapsed_ms": int((time.monotonic() - started) * 1000),
        }

def fetch(url: str, timeout: float, cookie_header: str = "", referer: str = "") -> Fetch:
    """Fetch with curl so DNS, connect, and total request time have hard bounds."""
    started = time.monotonic()
    timeout = max(1.0, float(timeout))
    meta_path = None
    body_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="feed-meta-", delete=False) as meta_fp, tempfile.NamedTemporaryFile(prefix="feed-body-", delete=False) as body_fp:
            meta_path = meta_fp.name
            body_path = body_fp.name
        command = [
            "curl", "--silent", "--show-error", "--location", "--compressed",
            "--connect-timeout", "12", "--max-time", str(int(timeout)),
            "-A", UA,
            "-H", "Accept: application/xml, application/rss+xml, text/xml, text/plain;q=0.9, */*;q=0.1",
            "-H", "Accept-Language: en-IN,en;q=0.9",
            "-H", "Cache-Control: no-cache",
            *([ "-H", f"Cookie: {cookie_header}" ] if cookie_header else []),
            *([ "-H", f"Referer: {referer}" ] if referer else []),
            "-o", body_path,
            "-w", "%{http_code}\\n%{content_type}\\n%{url_effective}\\n",
            url,
        ]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=timeout + 8, check=False)
        meta = proc.stdout.splitlines()
        status = int(meta[0]) if meta and meta[0].isdigit() else 0
        content_type = meta[1] if len(meta) > 1 else ""
        final_url = meta[2] if len(meta) > 2 else url
        body = Path(body_path).read_bytes() if body_path else b""
        error = None if proc.returncode == 0 else ("curl_timeout" if proc.returncode == 28 else f"curl_exit_{proc.returncode}")
        return Fetch(url, final_url, status, content_type, body, int((time.monotonic()-started)*1000), error)
    except subprocess.TimeoutExpired:
        return Fetch(url, url, 0, "", b"", int((time.monotonic()-started)*1000), "curl_process_timeout")
    except Exception as exc:
        return Fetch(url, url, 0, "", b"", int((time.monotonic()-started)*1000), type(exc).__name__)
    finally:
        for path in (meta_path, body_path):
            if path:
                try:
                    Path(path).unlink(missing_ok=True)
                except OSError:
                    pass


def _local(tag: object) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def validate_xml(body: bytes, content_type: str) -> Validation:
    if not body:
        return Validation(False, "empty", 0, 0, ("empty_body",))
    raw = body
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            return Validation(False, "gzip_invalid", 0, 0, ("gzip_parse_error",))
    text = raw.decode("utf-8", "replace")
    prefix = text.lstrip("\ufeff \r\n\t")
    if not prefix.startswith(("<?xml", "<rss", "<feed", "<channel", "<urlset", "<sitemapindex")):
        return Validation(False, "non_xml", 0, 0, ("not_xml_looking",))
    lower = prefix[:16000].lower()
    if any(marker in lower for marker in BLOCK_MARKERS):
        return Validation(False, "blocked", 0, 0, ("challenge_or_access_denied",))
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return Validation(False, "invalid_xml", 0, 0, ("xml_parse_error",))
    root_name = _local(root.tag)
    if root_name in SITEMAP_ROOTS:
        return Validation(False, "sitemap", 0, 0, ("sitemap_excluded",))
    items = [n for n in root.iter() if _local(n.tag) in ITEM_TAGS]
    ns_fields = {_local(n.tag) for n in root.iter() if isinstance(n.tag, str) and n.tag.startswith("{"+GOOGLE_NS+"}")}
    valid_items = 0
    for item in items:
        google_fields = {
            _local(n.tag)
            for n in item.iter()
            if isinstance(n.tag, str) and n.tag.startswith("{"+GOOGLE_NS+"}")
        }
        rss_fields = {
            _local(n.tag)
            for n in item
            if isinstance(n.tag, str) and not n.tag.startswith("{")
        }
        # Google Merchant RSS 2.0 permits predefined RSS title/link alongside
        # Google namespace attributes. ID and price remain Google attributes.
        title_ok = "title" in google_fields or "title" in rss_fields
        link_ok = "link" in google_fields or "link" in rss_fields
        if {"id", "price"}.issubset(google_fields) and title_ok and link_ok:
            valid_items += 1
    reasons = (f"root={root_name}", f"items={len(items)}", f"valid_items={valid_items}", f"google_fields={len(ns_fields)}")
    return Validation(bool(valid_items), "rss_or_atom" if root_name in {"rss","feed","channel"} else "xml", len(items), len(ns_fields), reasons, hashlib.sha256(raw).hexdigest() if valid_items else "")


def _explicit_http_url(root: str, raw: str) -> str | None:
    raw = html.unescape(str(raw or "")).strip().rstrip(".,);")
    if not raw:
        return None
    try:
        u = urllib.parse.urljoin(root.rstrip("/") + "/", raw)
        p = urllib.parse.urlsplit(u)
        host = (p.hostname or "").lower().rstrip(".")
        if p.scheme not in {"http", "https"} or not host or p.username or p.password:
            return None
        if host in {"localhost", "localhost.localdomain"} or host.endswith((".local", ".internal", ".lan")):
            return None
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return None
        except ValueError:
            pass
        return u
    except ValueError:
        return None


def extract_explicit_feed_urls(text: str, root: str) -> tuple[str, ...]:
    """Recover feed URLs explicitly declared by the storefront/config.
    Unlike generic link discovery, explicit feed fields may point to a
    third-party feed host; those URLs are still live-validated as XML.
    """
    decoded = html.unescape(text or "")
    found: set[str] = set()

    key_re = re.compile(
        r"(?:feed[_-]?(?:url|file|path)|xml[_-]?url|export[_-]?url|"
        r"product[_-]?feed|google[_-]?feed|merchant[_-]?feed|shopping[_-]?feed)"
        r"[\"']?\s*[:=]\s*[\"']([^\"']+)[\"']",
        re.I,
    )
    for m in key_re.finditer(decoded):
        u = _explicit_http_url(root, m.group(1))
        if u and re.search(r"(?:feed|merchant|shopping|google|xml|woocommerce)", u, re.I):
            found.add(u)

    for tag in re.findall(r"<link\b[^>]*>", decoded, re.I):
        low = tag.lower()
        if "alternate" not in low or not re.search(r"(?:rss|atom|xml)", low):
            continue
        m = re.search(r'href\s*=\s*["\']([^"\']+)["\']', tag, re.I)
        if not m:
            continue
        u = _explicit_http_url(root, m.group(1))
        if u:
            found.add(u)

    return tuple(sorted(found))


def extract_urls(text: str, root: str) -> tuple[str, ...]:
    decoded = html.unescape(text or "")
    raw: set[str] = set()
    for pattern in (
        r'https?://[^\s<>"\'\]\[)]+',
        r'(?:href|src|url|feedUrl|feed_url|feedURL|product_feed|google_feed)\s*[:=]\s*[\'"]([^\'"]+)[\'"]',
    ):
        for match in re.finditer(pattern, decoded, re.I):
            raw.add(match.group(1) if match.lastindex else match.group(0))
    return tuple(sorted({
        u for x in raw
        if re.search(r'\.xml(?:\.gz)?(?:[?#].*)?$|feed|merchant|shopping|woocommerce_gpf', x, re.I)
        for u in [absolute(root, x)]
        if u
    }))


def ctxfeed_urls(text: str, root: str) -> tuple[str, ...]:
    """Extract feed URLs/names exposed by public CTXFeed metadata endpoints."""
    try:
        data = json.loads(html.unescape(text or ""))
    except (TypeError, json.JSONDecodeError):
        return ()
    found: set[str] = set()

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                key_l = str(key).lower()
                if isinstance(value, str):
                    raw = value.strip()
                    if key_l in {"feed_url","feed_file","file_url","feed_path","xml_url","export_url","url"} and raw:
                        u = absolute(root, raw)
                        if u and re.search(r"(feed|merchant|shopping|google|woocommerce_gpf|\.xml)", u, re.I):
                            found.add(u)
                    if key_l in {"feed_name","filename","file","name"} and re.fullmatch(r"[A-Za-z0-9._-]{3,150}", raw):
                        for pattern in (
                            f"/?woo_feed={urllib.parse.quote(raw)}&wt=xml",
                            f"/?feed={urllib.parse.quote(raw)}",
                            f"/wp-content/uploads/woo-feed/google/xml/{urllib.parse.quote(raw)}.xml",
                            f"/wp-content/uploads/woo-feed/xml/{urllib.parse.quote(raw)}.xml",
                        ):
                            u = absolute(root, pattern)
                            if u:
                                found.add(u)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)
    return tuple(sorted(found))


def rest_feed_candidates(text: str, root: str) -> tuple[str, ...]:
    """Inspect the public WordPress REST index for feed-related routes.
    Route discovery is public metadata only; every route remains a candidate
    until the live native Google XML validator accepts its response.
    """
    try:
        data = json.loads(html.unescape(text or ""))
    except (TypeError, json.JSONDecodeError):
        return ()
    found: set[str] = set()
    route_keys = (
        "route", "namespace", "feed", "feed_url", "feed_file", "feed_path",
        "xml", "xml_url", "export", "export_url", "google", "merchant",
        "shopping", "product-feed", "product_feed", "ctxfeed", "gpf",
    )
    def maybe_add(raw: str) -> None:
        raw = str(raw or "").strip()
        if not raw.startswith("/"):
            return
        low = raw.lower()
        if not any(k in low for k in route_keys):
            return
        u = absolute(root, raw)
        if u:
            found.add(u)

    def walk(obj: object) -> None:
        if isinstance(obj, dict):
            for key, value in obj.items():
                k = str(key).lower()
                if k == "routes" and isinstance(value, dict):
                    for route in value:
                        maybe_add(str(route))
                elif isinstance(value, str):
                    if k in {"route", "namespace"} or any(tok in k for tok in ("feed", "google", "merchant", "shopping", "xml", "export")):
                        maybe_add(value)
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)

    walk(data)
    return tuple(sorted(found)[:200])


def directory_urls(text: str, root: str) -> tuple[str, ...]:
    decoded = html.unescape(text or "")
    found: set[str] = set()
    for x in re.findall(r'href=["\']([^"\']+)["\']', decoded, re.I):
        u = absolute(root, x)
        if u and urllib.parse.urlsplit(u).path.lower().endswith((".xml", ".xml.gz")):
            found.add(u)
    for x in re.findall(r'https?://[^\s<>"\'\]\[)]+\.xml(?:\.gz)?(?:[?#][^\s<>"\'\]\[)]*)?', decoded, re.I):
        u = absolute(root, x)
        if u:
            found.add(u)
    return tuple(sorted(found))


def feed_priority(url: str) -> tuple[int, int, str]:
    """Lower values are preferred: canonical full GPF, canonical permalink, static XML, partial GPF."""
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    path = parsed.path.rstrip("/")
    is_gpf = "woocommerce_gpf" in query or "woocommerce_gpf" in parsed.query
    has_slice = "gpf_start" in query or "gpf_limit" in query
    if is_gpf and not has_slice and path in {"", "/"}:
        return (0, 0, url)
    if not has_slice and path == "/woocommerce_gpf/google":
        return (1, 0, url)
    if parsed.path.lower().endswith((".xml", ".xml.gz")):
        return (2, 0, url)
    if is_gpf:
        limit = int((query.get("gpf_limit") or ["999999"])[0] or "999999")
        return (3, -min(limit, 999999), url)
    return (4, 0, url)


def filename_transport_sentinel(
    root: str,
    cookie_header: str,
    referer: str,
) -> tuple[bool, dict[str, object]]:
    """Return whether a host appears reachable enough to justify a large filename sweep."""
    sentinel_paths = (
        "/wp-content/uploads/google.xml",
        "/wp-content/uploads/google-feed.xml",
        "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
        "/wp-content/uploads/woo-feed/google/xml/google.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
        "/wp-content/uploads/wppfm-feeds/google.xml",
        "/google.xml",
        "/feed.xml",
    )
    records: list[dict[str, object]] = []
    for path in sentinel_paths:
        result = fetch(
            urllib.parse.urljoin(root.rstrip("/") + "/", path.lstrip("/")),
            4.0,
            cookie_header,
            referer,
        )
        records.append({"path": path, "status": result.status, "content_type": result.content_type})
        if result.status == 200:
            validation = validate_xml(result.body, result.content_type)
            if validation.valid:
                return True, {"mode": "validated", "records": records}
            # A reachable 200 response means the upload surface is probeable,
            # even when this particular name is not the feed.
            return True, {"mode": "reachable", "records": records}
    blocked = sum(1 for r in records if r["status"] in {401,403,429})
    # Treat a complete sentinel block as host-level transport blocking.
    if blocked == len(records):
        return False, {"mode": "blocked", "records": records}
    return True, {"mode": "mixed", "records": records}


def batch_first_valid(
    urls: list[str],
    timeout: float,
    workers: int,
    records: list[dict[str, object]],
    cookie_header: str = "",
    referer: str = "",
    allow_external: bool = False,
    chunk_size: int = 128,
) -> str | None:
    """Probe a large candidate set in bounded chunks and stop on the first valid native feed."""
    if not urls:
        return None
    ordered = list(dict.fromkeys(urls))
    for offset in range(0, len(ordered), max(1, chunk_size)):
        chunk = ordered[offset:offset + max(1, chunk_size)]
        pool = concurrent.futures.ThreadPoolExecutor(max_workers=workers)
        futures = {pool.submit(fetch, u, timeout, cookie_header, referer): u for u in chunk}
        try:
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                validation = validate_xml(result.body, result.content_type) if result.status == 200 else Validation(False, "not_checked", 0, 0, ())
                records.append({
                    "requested_url": result.requested_url,
                    "final_url": result.final_url,
                    "status": result.status,
                    "content_type": result.content_type,
                    "elapsed_ms": result.elapsed_ms,
                    "error": result.error,
                    "validation": asdict(validation),
                })
                if result.status == 200 and validation.valid and (
                    allow_external or same_host(result.final_url, result.requested_url)
                ):
                    for pending in futures:
                        if not pending.done():
                            pending.cancel()
                    pool.shutdown(wait=False, cancel_futures=True)
                    return result.final_url
        finally:
            pool.shutdown(wait=False, cancel_futures=True)
    return None


def batch(urls: list[str], timeout: float, workers: int, records: list[dict[str, object]], cookie_header: str = "", referer: str = "", allow_external: bool = False) -> str | None:
    if not urls:
        return None
    valid: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(fetch, u, timeout, cookie_header, referer): u for u in urls}
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
            validation = validate_xml(result.body, result.content_type) if result.status == 200 else Validation(False, "not_checked", 0, 0, ())
            records.append({
                "requested_url": result.requested_url,
                "final_url": result.final_url,
                "status": result.status,
                "content_type": result.content_type,
                "elapsed_ms": result.elapsed_ms,
                "error": result.error,
                "validation": asdict(validation),
            })
            if result.status == 200 and validation.valid and (allow_external or same_host(result.final_url, result.requested_url)):
                valid.append(result.final_url)
    return min(valid, key=feed_priority) if valid else None


def load_learned_feed_patterns(paths: tuple[Path, ...]) -> tuple[str, ...]:
    """Extract only patterns from previously verified native feed URLs.
    Patterns are never trusted by themselves: probe_site re-fetches and
    re-validates every learned candidate on the new retailer.
    """
    learned: set[str] = set()
    for base in paths:
        if not base.exists():
            continue
        for path in base.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                urls = []
                if data.get("native_feed_url"):
                    urls.append(str(data["native_feed_url"]))
                records = data.get("evidence", {}).get("records", []) if isinstance(data.get("evidence"), dict) else []
                for record in records if isinstance(records, list) else []:
                    if isinstance(record, dict):
                        validation = record.get("validation", {})
                        if isinstance(validation, dict) and record.get("requested_url"):
                            # Learn both verified feeds and strong near-hit XML/feed paths
                            # (product rows present, not HTML/challenge/sitemap). Every learned
                            # path is re-fetched and re-validated on the next site.
                            fmt = str(validation.get("format") or "")
                            products = int(validation.get("product_items") or 0)
                            is_near_hit = fmt in {"rss_or_atom", "xml"} and products > 0
                            if validation.get("valid") or is_near_hit:
                                urls.append(str(record["requested_url"]))
                for raw in urls:
                    try:
                        p = urllib.parse.urlsplit(raw)
                    except ValueError:
                        continue
                    if p.scheme not in {"http", "https"} or not p.path:
                        continue
                    learned.add(p.path or "/")
                    if p.query:
                        learned.add(f"{p.path or '/'}?{p.query}")
    return tuple(sorted(learned)[:120])


def validation_candidate_groups(
    discovered: set[str],
    explicit_feed_candidates: set[str],
    root: str,
) -> tuple[list[str], list[str]]:
    """Split discovered feed candidates into same-site and explicitly-declared external URLs."""
    candidates = sorted(
        u for u in discovered
        if urllib.parse.urlsplit(u).path.lower().endswith((".xml", ".xml.gz"))
        or re.search(r"(feed|merchant|shopping|woocommerce_gpf|google|woo[-_]?feed|wppfm)", u, re.I)
    )[:240]
    same_site = [u for u in candidates if same_host(u, root)]
    explicit_external = [
        u for u in sorted(explicit_feed_candidates)
        if u in candidates and not same_host(u, root)
    ]
    return same_site, explicit_external


def probe_site(site: str, root: str, learned_paths: tuple[str, ...] = ()) -> SiteResult:
    started = time.monotonic()
    records: list[dict[str, object]] = []
    discovered: set[str] = set()
    explicit_feed_candidates: set[str] = set()
    session_cookie_header = warm_site_session(root)
    plugin_signals = plugin_fingerprint(root, session_cookie_header) if session_cookie_header else ()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 15.0, session_cookie_header, root) for p in DISCOVERY_PATHS]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result.status == 200 and result.body:
                text = result.body.decode("utf-8", "replace")
                discovered.update(extract_urls(text, root))
                explicit_feed_candidates.update(extract_explicit_feed_urls(text, root))
                discovered.update(extract_explicit_feed_urls(text, root))
                discovered.update(rest_feed_candidates(text, root))

    ctx_candidates: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ctx_results = pool.map(lambda p: fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 12.0, session_cookie_header, root), CTXFEED_PATHS)
        for result in ctx_results:
            if result.status == 200 and result.body:
                ctx_candidates.update(ctxfeed_urls(result.body.decode("utf-8", "replace"), root))
                ctx_candidates.update(rest_feed_candidates(result.body.decode("utf-8", "replace"), root))

    fast_candidates = [urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in FAST_PATHS]
    fast_candidates.extend(
        urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/"))
        for p in learned_paths
    )
    fast_candidates.extend(sorted(ctx_candidates))
    # Learn plugin-shaped paths from previous verified native feeds and current fingerprints.
    if "adtribes" in plugin_signals:
        fast_candidates.extend([
            "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
            "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
            "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
        ])
    if "ctxfeed" in plugin_signals:
        fast_candidates.extend([
            "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
            "/wp-content/uploads/woo-feed/google/xml/google.xml",
            "/wp-content/uploads/woo-feed/google/google-shopping.xml",
        ])
    verified = batch(list(dict.fromkeys(fast_candidates)), 20.0, 8, records, session_cookie_header, root)
    if verified is None:
        verified = batch([urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in SLOW_GPF_PATHS], 105.0, 4, records, session_cookie_header, root)
    if verified is None:
        verified = batch([urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in MEDIUM_PATHS], 45.0, 8, records, session_cookie_header, root)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        directory_results = pool.map(lambda p: (p, fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 12.0, session_cookie_header, root)), DIRECTORIES)
        for directory, result in directory_results:
            if result.status == 200 and result.body:
                discovered.update(directory_urls(result.body.decode("utf-8", "replace"), root))

    browser_meta: dict[str, object] = {"available": False}
    browser_candidates: tuple[str, ...] = ()
    if verified is None:
        browser_probe_candidates = tuple(
            urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/"))
            for p in list(FAST_PATHS) + list(MEDIUM_PATHS) + list(SLOW_GPF_PATHS)
        )
        browser_cookie_header, browser_candidates, browser_meta = browser_session_discover(
            root, candidate_urls=tuple(dict.fromkeys(browser_probe_candidates))
        )
        if browser_cookie_header:
            session_cookie_header = browser_cookie_header
        discovered.update(browser_candidates)

    historical_candidates: tuple[str, ...] = ()
    historical_meta: dict[str, object] = {"queried": False, "candidate_count": 0}
    if verified is None:
        historical_candidates = historical_feed_discover(root)
        historical_meta = {"queried": True, "candidate_count": len(historical_candidates)}
        discovered.update(historical_candidates)

    filename_sweep_candidates: tuple[str, ...] = ()
    filename_sweep_meta: dict[str, object] = {"attempted": False, "candidate_count": 0}
    if verified is None:
        sweep_allowed, sentinel = filename_transport_sentinel(root, session_cookie_header, root)
        filename_sweep_candidates = generated_upload_feed_candidates(root, site)
        filename_sweep_meta = {
            "attempted": bool(sweep_allowed),
            "candidate_count": len(filename_sweep_candidates),
            "sentinel": sentinel,
        }
        if sweep_allowed:
            verified = batch_first_valid(list(filename_sweep_candidates), 3.0, 64, records, session_cookie_header, root, chunk_size=256)

    if verified is None and discovered:
        same_site, explicit_external = validation_candidate_groups(
            discovered, explicit_feed_candidates, root
        )
        verified = batch(same_site, 60.0, 8, records, session_cookie_header, root)
        if verified is None and explicit_external:
            verified = batch(explicit_external, 60.0, 8, records, session_cookie_header, root, True)

    status_codes = [int(r.get("status") or 0) for r in records]
    status = "verified_native" if verified else ("transport_blocked" if any(x in {401,403,429} for x in status_codes) else "candidate_negative_or_unverified")
    evidence = {
        "native_only": True,
        "verified": bool(verified),
        "tested_candidate_count": len(records),
        "discovered_url_count": len(discovered),
        "explicit_feed_candidate_count": len(explicit_feed_candidates),
        "validated_explicit_feed_candidate_count": len([r for r in records if r.get("requested_url") in explicit_feed_candidates]),
        "explicit_feed_candidates": sorted(explicit_feed_candidates)[:100],
        "plugin_signals": list(plugin_signals),
        "same_site_session_established": bool(session_cookie_header),
        "browser_discovery": browser_meta,
        "historical_discovery": historical_meta,
        "filename_sweep": filename_sweep_meta,
        "records": records,
    }
    return SiteResult(site, root, status, verified, evidence, round(time.monotonic() - started, 3))


def run_shard(shard: int, shards: int, output_dir: Path, targets: tuple[tuple[str, str], ...] | None = None, learned_paths: tuple[str, ...] = ()) -> list[SiteResult]:
    started = time.monotonic()
    target_set = TARGETS if targets is None else targets
    selected = [target for idx, target in enumerate(target_set) if idx % shards == shard]
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[SiteResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        future_map = {pool.submit(probe_site, site, root, learned_paths): (site, root) for site, root in selected}
        for future in concurrent.futures.as_completed(future_map):
            site_name, site_root_url = future_map[future]
            try:
                result = future.result()
            except Exception as exc:
                # Preserve complete 32-site coverage even when one site's discovery
                # code has a defect; the aggregate manifest remains truthful.
                result = SiteResult(
                    site_name,
                    site_root_url,
                    "execution_error",
                    None,
                    {
                        "native_only": True,
                        "verified": False,
                        "tested_candidate_count": 0,
                        "discovered_url_count": 0,
                        "error_type": type(exc).__name__,
                        "error": str(exc)[:500],
                    },
                    round(time.monotonic() - started, 3),
                )
            results.append(result)
            slug = re.sub(r"[^a-z0-9]+", "-", result.site.lower()).strip("-")
            (output_dir / f"{slug}.json").write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
    results.sort(key=lambda x: x.site.lower())
    (output_dir / "verified-native-feed-urls.tsv").write_text(
        "\n".join(f"{r.site}\t{r.native_feed_url}" for r in results if r.native_feed_url) + ("\n" if any(r.native_feed_url for r in results) else ""),
        encoding="utf-8",
    )
    return results


def aggregate(root: Path, output_file: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for path in sorted(root.rglob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and "site" in data and "root" in data:
            rows.append(data)
    rows.sort(key=lambda x: (str(x["site"]).lower(), bool(x.get("native_feed_url"))))
    deduped: dict[str, dict[str, object]] = {}
    for row in rows:
        site_key = str(row.get("site") or "").strip().lower()
        if not site_key:
            continue
        prior = deduped.get(site_key)
        if prior is None or (bool(row.get("native_feed_url")) and not bool(prior.get("native_feed_url"))):
            deduped[site_key] = row
        elif prior is not None and bool(row.get("native_feed_url")) == bool(prior.get("native_feed_url")):
            # Prefer the later staged round/file path by deterministic traversal order.
            deduped[site_key] = row
    rows = sorted(deduped.values(), key=lambda x: str(x["site"]).lower())
    manifest = {
        "schema": "woocommerce-native-google-feed-manifest/v2",
        "native_only": True,
        "no_reconstruction": True,
        "sites_total": len(TARGETS),
        "sites_present": len(rows),
        "verified_native_feed_count": sum(bool(x.get("native_feed_url")) for x in rows),
        "verified_native_feeds": [{"site": x["site"], "url": x["native_feed_url"]} for x in rows if x.get("native_feed_url")],
        "results": rows,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, choices=range(8))
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--output-dir", default="out/native-google-feed-hunt")
    parser.add_argument("--aggregate-dir")
    parser.add_argument("--output-file", default="out/native-google-feed-manifest.json")
    parser.add_argument("--only-sites", help="Comma-separated site names from TARGETS")
    parser.add_argument("--learn-from", action="append", default=[], help="Prior evidence directory to learn verified feed path/query patterns from")
    args = parser.parse_args()

    if args.aggregate_dir:
        manifest = aggregate(Path(args.aggregate_dir), Path(args.output_file))
        print(json.dumps({k: manifest[k] for k in ("sites_total","sites_present","verified_native_feed_count","verified_native_feeds")}, indent=2))
        return 0
    if args.shard is None:
        raise SystemExit("--shard is required unless --aggregate-dir is used")
    if not 0 <= args.shard < args.shards:
        raise SystemExit("invalid shard")
    selected_targets = None
    learned_paths = load_learned_feed_patterns(tuple(Path(p) for p in args.learn_from))
    if args.only_sites:
        requested = {x.strip().lower() for x in args.only_sites.split(",") if x.strip()}
        if not requested:
            raise SystemExit("--only-sites must contain at least one site name")
        selected_targets = tuple((site, url) for site, url in TARGETS if site.lower() in requested)
        missing = requested - {site.lower() for site, _ in selected_targets}
        if missing:
            raise SystemExit("unknown --only-sites: " + ", ".join(sorted(missing)))
    results = run_shard(args.shard, args.shards, Path(args.output_dir), selected_targets, learned_paths)
    print(json.dumps({
        "shard": args.shard,
        "sites": len(results),
        "target_scope": [r.site for r in results],
        "learned_path_count": len(learned_paths),
        "verified_native_feed_count": sum(bool(r.native_feed_url) for r in results),
        "verified_native_feeds": [{"site": r.site, "url": r.native_feed_url} for r in results if r.native_feed_url],
        "statuses": {r.site: r.status for r in results},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
