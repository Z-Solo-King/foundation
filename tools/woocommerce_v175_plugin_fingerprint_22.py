#!/usr/bin/env python3
from __future__ import annotations

"""
WooCommerce V175-derived plugin fingerprint + native Google-feed recovery harness.

The attached extract_universal_V175.py is the source/design authority for:
- clearance-aware browser recovery
- persistent-cookie semantics
- browser/XHR discovery
- transport/provenance separation
- bounded recovery budgets
- public-only acquisition

V175 source SHA-256: 33d651b329c20372db40026c0626a3227408096beb910c1d1069266af5cc1b15

This focused harness deliberately does NOT import the 1.5 MB monolith at runtime.
It preserves the V175 evidence contracts while enforcing the repository acceptance boundary:
- Chromium + Firefox/Gecko + WebKit clean browser passes
- public API/XHR discovery without clearance-cookie replay
- optional Cloudflare Browser Run and Browserless adapters
- passive robots/sitemap + historical index discovery
- plugin fingerprint normalization with provenance-aware confidence
- plugin-specific native Google XML candidate generation
- strict payload validation

Important: challenge/clearance encounters are diagnostic only. No clearance cookies, CAPTCHA state,
or anti-bot bypass state are replayed or admitted into native-feed verification.
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit, quote

import httpx


TARGETS = [
    ("Aarna Computers", "https://aarnacomputers.com"),
    ("Ads Store", "https://adsstore.in"),
    ("EZPZ Solutions", "https://www.ezpzsolutions.in"),
    ("GamesNComps", "https://gamesncomps.com"),
    ("hotshiftpc", "https://hotshiftpc.com"),
    ("ithunt", "https://ithunt.in"),
    ("KC Computers", "https://kccomputers.co.in"),
    ("KRG KART", "https://krgkart.com"),
    ("Kryptronix Gaming", "https://kryptronix.in"),
    ("NCL Computer", "https://nclcomputer.com"),
    ("PC Kumar Infotech", "https://pckumar.in"),
    ("PCHubShop", "https://www.pchubshop.com"),
    ("Prime ABGB", "https://www.primeabgb.com"),
    ("SCL Gaming", "https://sclgaming.in"),
    ("Variety Infotech", "https://varietyinfotech.com"),
    ("Viper PC", "https://viperpc.in"),
    ("AULA India", "https://aulaindia.com"),
    ("Cosmic Byte", "https://www.thecosmicbyte.com"),
    ("Meckeys", "https://www.meckeys.com"),
    ("StacksKB", "https://stackskb.com"),
    ("Theproaudio", "https://www.theproaudio.com"),
]

KNOWN_10 = {
    "pcstudio.in",
    "quickincomputers.com",
    "avikaretails.com",
    "geekbees.in",
    "ninjadog.in",
    "networkitstore.in",
    "mynexusinfosys.com",
    "solankienterprises.com",
    "onlyssd.com",
    "itgadgetsonline.com",
}

PLUGIN_RULES: List[Tuple[str, Tuple[str, ...]]] = [
    ("woocommerce_google_product_feed", (
        "woocommerce google product feed",
        "woocommerce_gpf",
        "woocommerce-gpf",
        "woocommerce-google-product-feed",
        "google_product_feed",
        "google-product-feed",
        "lw_woocommerce_gpf",
    )),
    ("ctx_feed_webappick", (
        "ctx feed", "ctx-feed", "webappick", "woo_feed", "woo-feed",
        "woo feed", "woo_feed-", "webappick-product-feed-for-woocommerce",
    )),
    ("adtribes_product_feed_pro", (
        "product feed pro", "adtribes", "woo-product-feed-pro",
        "product-feed-pro", "woo-product-feed-pro-for-woocommerce",
    )),
    ("wpfm_product_feed_manager", (
        "product feed manager", "wppfm", "wppfm-feeds", "wpfm/v1",
        "product-feed-manager-for-woocommerce",
    )),
    ("webtoffee_product_feed", (
        "webtoffee", "webtoffee_product_feed", "webtoffee-product-feed",
        "webtoffee-product-feed-for-woocommerce",
    )),
    ("codesolz_merchant_feed_booster", (
        "codesolz", "codesolz-feeds", "merchant feed booster",
        "merchant-feed-booster-lite-for-woocommerce",
    )),
    ("feedcraft", (
        "feedcraft", "feedcraft-product-feed", "thebasics-product-feed",
    )),
    ("google_for_woocommerce", (
        "google-listings-and-ads", "google for woocommerce", "wc/gla",
        "google_merchant_center", "google merchant center",
    )),
]

GENERIC_FEED_PATHS = [
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=10",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=50",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
    "/google.xml",
    "/google_feed.xml",
    "/google-feed.xml",
    "/google_base.xml",
    "/googlebase.xml",
    "/google-products.xml",
    "/google-product-feed.xml",
    "/google_product_feed.xml",
    "/google-shopping.xml",
    "/google-shopping-feed.xml",
    "/google-merchant.xml",
    "/google-merchant-feed.xml",
    "/merchant.xml",
    "/merchant-feed.xml",
    "/merchant_feed.xml",
    "/gpf.xml",
    "/product-feed.xml",
    "/products-feed.xml",
    "/feed_products.xml",
    "/feed.xml",
    "/feed/google.xml",
    "/feed/google-feed.xml",
    "/feed/google-products.xml",
    "/feed/google-product-feed.xml",
    "/feed/google-shopping.xml",
    "/feed/google-shopping-feed.xml",
    "/feed/merchant.xml",
    "/feed/merchant-feed.xml",
    "/feeds/google.xml",
    "/feeds/google-feed.xml",
    "/feeds/google-products.xml",
    "/feeds/google-product-feed.xml",
    "/feeds/google-shopping.xml",
    "/feeds/google-shopping-feed.xml",
    "/feeds/merchant.xml",
    "/feeds/merchant-feed.xml",
    "/catalog/feed",
    "/catalog/feed.xml",
    "/catalog/google.xml",
    "/media/feed/google.xml",
    "/wp-content/uploads/google.xml",
    "/wp-content/uploads/google-feed.xml",
    "/wp-content/uploads/google_product_feed.xml",
    "/wp-content/uploads/google-shopping.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/wp-content/uploads/woo-feed/google.xml",
    "/wp-content/uploads/woo-feed/google/feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/feed.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/feed.xml",
    "/wp-json/google-product-feed/v1/xml",
    "/wp-json/google-feed/v1/xml",
    "/wp-json/woo-feed/v1/google.xml",
]

PLUGIN_CANDIDATES = {
    "woocommerce_google_product_feed": [
        "/?woocommerce_gpf=google",
        "/woocommerce_gpf/google",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
        "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
    ],
    "ctx_feed_webappick": [
        "/?woo_feed=google&wt=xml",
        "/?woo_feed=google_shopping&wt=xml",
        "/?woo_feed=google-shopping&wt=xml",
        "/?woo_feed=google_merchant&wt=xml",
    ],
    "adtribes_product_feed_pro": [
        "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
        "/wp-content/uploads/woo-product-feed-pro/google.xml",
    ],
    "wpfm_product_feed_manager": [
        "/wp-content/uploads/wppfm-feeds/google.xml",
        "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
        "/wp-content/uploads/wppfm-feeds/google-feed.xml",
        "/wp-content/uploads/wppfm-feeds/google_products.xml",
    ],
    "webtoffee_product_feed": [
        "/wp-content/uploads/webtoffee_product_feed/wt_Google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google-shopping_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml",
    ],
    "codesolz_merchant_feed_booster": [
        "/wp-content/uploads/codesolz-feeds/google.xml",
        "/wp-content/uploads/codesolz-feeds/google-products.xml",
        "/wp-content/uploads/codesolz-feeds/google-shopping.xml",
    ],
    "feedcraft": [
        "/wp-json/feedcraft-product-feed/v1/xml",
        "/wp-json/feedcraft-product-feed/v1/google.xml",
        "/wp-json/feedcraft-product-feed/v1/feed.xml",
        "/wp-json/feedcraft-product-feed/v1/google",
    ],
}

API_PATHS = [
    "/wp-json/",
    "/wp-json/wp/v2/types",
    "/wp-json/wc/store/v1/products?per_page=1",
    "/wp-json/wc/store/v1/products/",
    "/?rest_route=/wc/store/v1/products",
]
WC_REST_PATHS = [
    "/wp-json/wc/v1/products",
    "/wp-json/wc/v2/products",
    "/wp-json/wc/v3/products",
]

MAX_DIRECT_FEED_PROBES = max(10, int(os.getenv("MAX_DIRECT_FEED_PROBES", "40")))
MAX_INTERNAL_PAGES = max(0, min(2, int(os.getenv("MAX_INTERNAL_PAGES", "2"))))
PASSIVE_INDEX_ENABLED = os.getenv("PASSIVE_INDEX_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
WAYBACK_ENABLED = os.getenv("WAYBACK_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
COMMONCRAWL_ENABLED = os.getenv("COMMONCRAWL_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
CF_BROWSER_RUN_ENABLED = os.getenv("CF_BROWSER_RUN_ENABLED", "0").strip().lower() in {"1", "true", "yes"}

PASSIVE_FEED_HINT_RE = re.compile(
    r"(?:feed|google|merchant|shopping|woocommerce_gpf|woo_feed|wppfm|wpfm|webtoffee|adtribes|feedcraft|product-feed)",
    re.I,
)



@dataclass
class BrowserEvidence:
    engine: str
    status: int = 0
    challenge: bool = False
    challenge_encountered: bool = False
    cf_clearance: bool = False
    cookie_names: List[str] = None
    user_agent: str = ""
    html_len: int = 0
    visited_internal_urls: List[str] = None
    plugin_asset_slugs: List[str] = None
    namespaces: List[str] = None
    xhr_urls: List[str] = None
    resource_urls: List[str] = None
    error: str = ""

    def __post_init__(self):
        self.cookie_names = self.cookie_names or []
        self.visited_internal_urls = self.visited_internal_urls or []
        self.plugin_asset_slugs = self.plugin_asset_slugs or []
        self.namespaces = self.namespaces or []
        self.xhr_urls = self.xhr_urls or []
        self.resource_urls = self.resource_urls or []


@dataclass
class ApiEvidence:
    url: str
    status: int
    allow: str = ""
    content_type: str = ""
    namespaces: List[str] = None
    plugin_hits: List[str] = None
    body_read: bool = False
    error: str = ""

    def __post_init__(self):
        self.namespaces = self.namespaces or []
        self.plugin_hits = self.plugin_hits or []


def bare_host(url: str) -> str:
    h = (urlsplit(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def same_host(a: str, b: str) -> bool:
    return bare_host(a) == bare_host(b)


def is_challenge(status: int, body: str) -> bool:
    s = str(body or "")[:15000].lower()
    markers = (
        "just a moment", "cf-chl-", "cf-browser-verification", "cf-mitigated",
        "challenge-platform", "cf-turnstile", "cdn-cgi/challenge",
        "verify you are human", "attention required", "checking your browser",
        "access denied", "request blocked", "security rejection", "captcha",
        "turnstile",
    )
    if status in (403, 429, 430, 503, 520, 521, 522, 523, 524):
        return any(m in s for m in markers) or not s
    if status == 200 and any(m in s for m in markers):
        if "application/ld+json" in s and '"@type":"product"' in s:
            return False
        return True
    return False


def parse_plugin_slugs(text: str) -> List[str]:
    slugs = set(re.findall(r"/wp-content/plugins/([^/?#\"' <]+)/", text or "", re.I))
    return sorted(slugs)[:80]


def _normalize_namespace(value: str) -> str:
    # WordPress REST discovery may JSON-escape slashes as \\/.
    return str(value or "").replace(r"\/", "/").strip()


def parse_namespaces(text: str) -> List[str]:
    out = set()
    for m in re.finditer(r'"namespaces"\s*:\s*\[(.*?)\]', text or "", re.S):
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            n = _normalize_namespace(item)
            if n:
                out.add(n)
    for m in re.findall(r'"([A-Za-z0-9_.-]+(?:\\/|/)[A-Za-z0-9_.-]+)"', text or ""):
        n = _normalize_namespace(m)
        if any(k in n.lower() for k in ("feed", "wpfm", "woo", "google", "merchant", "ctx")):
            out.add(n)
    return sorted(out)


def find_plugin_hits(blobs: Iterable[str], plugin_slugs: Iterable[str], namespaces: Iterable[str]) -> Dict[str, List[str]]:
    """Return family hits using family-exclusive fingerprints where possible.

    Generic page copy such as "Google Merchant Center" is not sufficient to
    classify a Google-for-WooCommerce integration. Strong fingerprints must be
    present in a plugin asset slug, REST namespace, resource URL, or explicit
    family-specific endpoint signature.
    """
    all_text = "\n".join(str(x or "") for x in blobs).lower()
    evidence = set(str(x).lower() for x in plugin_slugs)
    evidence.update(str(x).lower() for x in namespaces)
    hits: Dict[str, List[str]] = {}

    exclusive = {
        "woocommerce_google_product_feed": (
            "woocommerce_gpf", "woocommerce-gpf", "woocommerce-google-product-feed",
            "google_product_feed", "google-product-feed", "lw_woocommerce_gpf",
        ),
        "ctx_feed_webappick": (
            "ctx feed", "ctx-feed", "webappick", "woo_feed", "woo-feed",
            "webappick-product-feed-for-woocommerce",
        ),
        "adtribes_product_feed_pro": (
            "adtribes", "woo-product-feed-pro", "product-feed-pro",
            "woo-product-feed-pro-for-woocommerce",
        ),
        "wpfm_product_feed_manager": (
            "wppfm", "wppfm-feeds", "wpfm/v1",
            "product-feed-manager-for-woocommerce",
        ),
        "webtoffee_product_feed": (
            "webtoffee", "webtoffee_product_feed", "webtoffee-product-feed",
            "webtoffee-product-feed-for-woocommerce",
        ),
        "codesolz_merchant_feed_booster": (
            "codesolz", "codesolz-feeds", "merchant-feed-booster",
        ),
        "feedcraft": ("feedcraft", "feedcraft-product-feed", "thebasics-product-feed"),
        "google_for_woocommerce": (
            "google-listings-and-ads", "wc/gla", "google_merchant_center_plugin",
        ),
    }

    for family, needles in PLUGIN_RULES:
        family_hits = []
        strong = exclusive.get(family, needles)

        for e in evidence:
            for n in strong:
                if n in e:
                    family_hits.append(e)
                    break

        for n in strong:
            if n in all_text:
                family_hits.append(n)

        if family == "google_for_woocommerce":
            family_hits = [
                x for x in family_hits
                if x in {"google-listings-and-ads", "wc/gla", "google_merchant_center_plugin"}
                or "google-listings-and-ads" in x
                or "wc/gla" in x
            ]

        if family_hits:
            hits[family] = sorted(set(family_hits))[:20]
    return hits

def plugin_family_confidence(hits: Dict[str, List[str]], plugin_slugs: Iterable[str], namespaces: Iterable[str]) -> str:
    """Prefer concrete plugin asset evidence over generic page text."""
    if not hits:
        return "low"
    slugs = {str(x).lower() for x in plugin_slugs}
    ns = {str(x).lower() for x in namespaces}
    strong = {
        str(needle).lower()
        for family, needles in PLUGIN_RULES
        if family in hits
        for needle in needles
    }
    if any(any(n in s for n in strong) for s in slugs):
        return "high"
    if any(any(n in x for n in strong) for x in ns):
        return "medium"
    return "low"


def query_feed_candidates(text: str, root: str) -> List[str]:
    """Recover public feed URLs expressed as query parameters even when the slug is random."""
    out = set()
    for m in re.finditer(r"(?:[?&])(woo_feed|woocommerce_gpf)=([^&#\"' <>]+)", text or "", re.I):
        key, value = m.group(1), m.group(2)
        if not value:
            continue
        prefix = "/?"
        if key.lower() == "woo_feed":
            out.add(urljoin(root + "/", prefix + f"woo_feed={value}&wt=xml"))
            out.add(urljoin(root + "/", prefix + f"woo_feed={value}"))
        else:
            out.add(urljoin(root + "/", prefix + f"woocommerce_gpf={value}"))
            if value.lower() == "google":
                for start in (0, 100):
                    out.add(urljoin(root + "/", prefix + f"woocommerce_gpf=google&gpf_start={start}&gpf_limit=100"))
    for raw in re.findall(r"https?://[^\s\"'<>]+", text or "", re.I):
        u = raw.rstrip("),.;")
        if same_host(u, root) and PASSIVE_FEED_HINT_RE.search(u):
            out.add(u)
    return sorted(out)[:120]


def discover_urls_from_xml_or_text(text: str, root: str) -> List[str]:
    urls = set(explicit_xml_candidates(text, root))
    urls.update(query_feed_candidates(text, root))
    for raw in re.findall(r"(?:href|src|loc)=['\"]([^'\"]+)['\"]", text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and PASSIVE_FEED_HINT_RE.search(u):
            urls.add(u)
    return sorted(urls)[:200]


def passive_sitemap_candidates(text: str, root: str) -> List[str]:
    out = set(discover_urls_from_xml_or_text(text, root))
    for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text or "", re.I):
        try:
            full = urljoin(root + "/", u)
        except Exception:
            continue
        if same_host(full, root) and PASSIVE_FEED_HINT_RE.search(full):
            out.add(full)
    return sorted(out)[:200]


def explicit_xml_candidates(text: str, root: str) -> List[str]:
    out = set()
    for raw in re.findall(r'https?://[^\s"\'<>]+', text or "", re.I):
        u = raw.rstrip("),.;")
        if not same_host(u, root):
            continue
        if re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I) or PASSIVE_FEED_HINT_RE.search(u):
            out.add(u)
    for raw in re.findall(r'''(?:href|src|loc)=["']([^"']+)["']''', text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and (re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I) or PASSIVE_FEED_HINT_RE.search(u)):
            out.add(u)
    return sorted(out)[:160]


def filter_explicit_feed_candidates(urls: Iterable[str]) -> List[str]:
    """Keep actual feed-like URLs, excluding sitemap/robots discovery documents."""
    out = set()
    for raw in urls:
        try:
            u = str(raw)
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if path.endswith("robots.txt") or "sitemap" in path:
            continue
        out.add(u)
    return sorted(out)[:160]


PLUGIN_FEED_DIRECTORIES = [
    "/wp-content/uploads/woo-feed/google/xml/",
    "/wp-content/uploads/woo-feed/google/",
    "/wp-content/uploads/woo-product-feed-pro/xml/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/webtoffee_product_feed/",
    "/wp-content/uploads/codesolz-feeds/",
    "/feeds/",
    "/feed/",
]


def public_directory_feed_candidates(text: str, root: str, directory: str) -> List[str]:
    """Discover generated XML files from a public directory index; never invent filenames."""
    out = set()
    base = urljoin(root + "/", directory.lstrip("/"))
    for raw in re.findall(r'''(?:href|data-href)=["']([^"']+)["']''', text or "", re.I):
        if raw in ("../", "./", "#"):
            continue
        try:
            u = urljoin(base, raw)
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if not same_host(u, root):
            continue
        if not (path.endswith(".xml") or path.endswith(".xml.gz")):
            continue
        # Known plugin output directories may use arbitrary/generated filenames.
        out.add(u)
    for raw in re.findall(r'https?://[^\s"\'<>]+', text or "", re.I):
        try:
            u = raw.rstrip("),.;")
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if same_host(u, root) and (path.endswith(".xml") or path.endswith(".xml.gz")):
            out.add(u)
    return sorted(out)[:120]


def native_verification_admissible(
    challenge_encountered: bool,
    clean_browser_success: bool,
    native_feed_verified: bool,
) -> bool:
    """Allow a standalone feed only when its own current payload is valid and public."""
    return bool(native_feed_verified or (clean_browser_success and not challenge_encountered))


def native_google_valid(body: bytes, content_type: str) -> Tuple[bool, int, str]:
    if not body:
        return False, 0, ""
    raw = body
    try:
        if raw[:2] == b"\x1f\x8b" or "gzip" in (content_type or "").lower():
            raw = gzip.decompress(raw)
    except Exception:
        return False, 0, ""
    text = raw.decode("utf-8", "ignore")
    low = text.lower()
    if not re.search(r"https?://base\.google\.com/ns/1\.0", low):
        return False, 0, ""
    if not re.search(r"<rss\b|<feed\b", low) or not re.search(r"<item\b|<entry\b", low):
        return False, 0, ""
    if re.search(r"just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser", low):
        return False, 0, ""
    ids = re.search(r"<g:id\b[^>]*>(.*?)</g:id>", text, re.S | re.I)
    titles = re.search(r"<g:title\b[^>]*>(.*?)</g:title>", text, re.S | re.I)
    links = re.search(r"<g:link\b[^>]*>(.*?)</g:link>", text, re.S | re.I)
    prices = re.search(r"<g:price\b[^>]*>(.*?)</g:price>", text, re.S | re.I)
    if not all((ids, titles, links, prices)):
        return False, 0, ""
    count = len(re.findall(r"<(?:item|entry)\b", text, re.I))
    return True, count, hashlib.sha256(raw).hexdigest()


async def http_get(client: httpx.AsyncClient, url: str, cookies: Dict[str, str], timeout: float = 25.0):
    try:
        r = await client.get(url, cookies=cookies, follow_redirects=True, timeout=timeout)
        body = await r.aread()
        return r.status_code, str(r.url), r.headers, body
    except Exception as e:
        return 0, url, {}, str(e).encode()


async def http_options(client: httpx.AsyncClient, url: str, cookies: Dict[str, str], timeout: float = 15.0):
    try:
        r = await client.options(url, cookies=cookies, follow_redirects=True, timeout=timeout)
        await r.aread()
        return r.status_code, str(r.url), r.headers
    except Exception:
        return 0, url, {}


async def api_surface(root: str, user_agent: str = "") -> Tuple[List[ApiEvidence], List[str], List[str]]:
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WooCommerceV175PluginRecovery/2026.09)",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }
    api_out: List[ApiEvidence] = []
    blobs: List[str] = []
    ns: List[str] = []
    async with httpx.AsyncClient(headers=headers) as client:
        for path in API_PATHS:
            url = urljoin(root + "/", path)
            st, final, hdrs, body = await http_get(client, url, {}, 20)
            txt = body.decode("utf-8", "ignore")[:500_000]
            if st == 200 and path.rstrip("/") in ("/wp-json", "/wp-json/"):
                blobs.append(txt)
                ns.extend(parse_namespaces(txt))
            api_out.append(ApiEvidence(
                url=url, status=st,
                allow=hdrs.get("allow", ""),
                content_type=hdrs.get("content-type", ""),
                namespaces=parse_namespaces(txt) if "wp-json" in path and st == 200 else [],
                plugin_hits=[],
                body_read=(path == "/wp-json/" and st == 200),
                error="" if st else txt[:180],
            ))
        for path in WC_REST_PATHS:
            url = urljoin(root + "/", path)
            st, final, hdrs = await http_options(client, url, {}, 12)
            api_out.append(ApiEvidence(
                url=url, status=st, allow=hdrs.get("allow", ""),
                content_type=hdrs.get("content-type", ""), body_read=False
            ))
    return api_out, blobs, sorted(set(ns))


def discover_internal_page_urls(text: str, root: str, limit: int = 2) -> List[str]:
    """Select a tiny same-host set of store/product/category pages for deeper public discovery."""
    scored: Dict[str, int] = {}
    for raw in re.findall(r'''(?:href|data-href|data-url)=["']([^"']+)["']''', text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
            parts = urlsplit(u)
        except Exception:
            continue
        if parts.scheme not in {"http", "https"} or not same_host(u, root) or parts.fragment:
            continue
        path = (parts.path or "/").lower()
        if any(x in path for x in ("/wp-admin", "/wp-login", "/cart", "/checkout", "/my-account", "/logout")):
            continue
        score = 0
        if "/product/" in path:
            score += 100
        if any(x in path for x in ("/shop", "/store", "/products", "/product-category", "/category/")):
            score += 70
        if "post_type=product" in (parts.query or "").lower():
            score += 80
        if path in {"/", ""}:
            score -= 50
        score -= min(len(path), 40) // 10
        scored[u.split("#", 1)[0]] = max(score, scored.get(u.split("#", 1)[0], -999))
    return sorted(scored, key=lambda u: (-scored[u], len(u), u))[:max(0, limit)]


async def browser_engine(root: str, engine: str):
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        return BrowserEvidence(engine=engine, error=f"playwright_not_installed:{e}"), {}, "", []
    try:
        async with async_playwright() as p:
            launcher = getattr(p, engine)
            browser = await launcher.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-IN",
                extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
            )
            page = await context.new_page()
            requests_seen: List[str] = []
            response_blobs: List[str] = []
            async def on_request(req):
                try:
                    if same_host(req.url, root):
                        requests_seen.append(req.url)
                except Exception:
                    pass

            async def on_response(resp):
                try:
                    u = resp.url
                    if not same_host(u, root):
                        return
                    hdrs = await resp.all_headers()
                    ct = hdrs.get("content-type", "")
                    interesting = (
                        "json" in ct.lower() or "xml" in ct.lower() or
                        any(x in u.lower() for x in (
                            "wp-json", "admin-ajax.php", "wc-ajax", "product", "catalog", "search", "feed",
                            "google", "merchant", "ctx", "wpfm", "webtoffee", "adtribes", "woo-feed", "feedcraft", 
                            "sitemap", "robots.txt", "/api/",
                        ))
                    )
                    if not interesting:
                        return
                    requests_seen.append(u)
                    if len(response_blobs) >= 40:
                        return
                    if any(x in u.lower() for x in ("feed", "google", "merchant", "woo_feed", "woocommerce_gpf", "wpfm", "webtoffee", "adtribes", "feedcraft", "admin-ajax.php")) or "json" in ct.lower() or "xml" in ct.lower():
                        try:
                            b = await resp.body()
                            if 0 < len(b) <= 350_000:
                                response_blobs.append(b.decode("utf-8", "ignore"))
                        except Exception:
                            pass
                except Exception:
                    pass

            page.on("request", on_request)
            page.on("response", on_response)
            try:
                resp = await page.goto(root, wait_until="domcontentloaded", timeout=45_000)
                await page.wait_for_timeout(2500)
            except Exception:
                resp = None
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                await page.wait_for_timeout(1200)
            except Exception:
                pass
            html = await page.content()
            visited_internal_urls: List[str] = []
            page_htmls = [html]
            status = getattr(resp, "status", 0) if resp else 0
            challenge = is_challenge(status, html)
            if status == 200 and not challenge and MAX_INTERNAL_PAGES:
                for internal_url in discover_internal_page_urls(html, root, MAX_INTERNAL_PAGES):
                    try:
                        internal_resp = await page.goto(internal_url, wait_until="domcontentloaded", timeout=25_000)
                        await page.wait_for_timeout(1000)
                        internal_html = await page.content()
                        visited_internal_urls.append(internal_url)
                        page_htmls.append(internal_html)
                        if is_challenge(getattr(internal_resp, "status", 0) if internal_resp else 0, internal_html):
                            challenge = True
                            break
                    except Exception:
                        continue
            html = "\\n".join(page_htmls)
            try:
                perf_urls = await page.evaluate("performance.getEntriesByType('resource').map(e => e.name)")
                if isinstance(perf_urls, list):
                    requests_seen.extend(str(x) for x in perf_urls if same_host(str(x), root))
            except Exception:
                perf_urls = []
            cookies = await context.cookies()
            cookie_names = sorted({str(c.get("name")) for c in cookies if c.get("name")})
            cookie_values = {str(c["name"]): str(c.get("value") or "") for c in cookies if c.get("name")}
            ua = ""
            try:
                ua = await page.evaluate("navigator.userAgent")
            except Exception:
                pass
            await browser.close()
            combined = html + "\n" + "\n".join(requests_seen) + "\n" + "\n".join(response_blobs)
            slugs = parse_plugin_slugs(combined)
            namespaces = parse_namespaces(combined)
            return BrowserEvidence(
                engine=engine,
                status=status,
                challenge=challenge,
                challenge_encountered=challenge,
                cf_clearance=("cf_clearance" in cookie_values or "__cf_bm" in cookie_values),
                cookie_names=cookie_names,
                user_agent=ua,
                html_len=len(html),
                visited_internal_urls=visited_internal_urls,
                plugin_asset_slugs=slugs,
                namespaces=namespaces,
                xhr_urls=sorted(set(requests_seen))[:300],
                resource_urls=sorted(set(str(x) for x in perf_urls if same_host(str(x), root)))[:300] if isinstance(perf_urls, list) else [],
                error="",
            ), {}, html, response_blobs
    except Exception as e:
        return BrowserEvidence(engine=engine, error=str(e)), {}, "", []


async def optional_cf_content(root: str) -> Tuple[Optional[str], Dict[str, Any]]:
    if not CF_BROWSER_RUN_ENABLED:
        return None, {"enabled": False, "reason": "disabled_by_default_or_scope"}
    account = os.getenv("CF_ACCOUNT_ID", "").strip()
    token = os.getenv("CF_API_TOKEN", "").strip()
    if not account or not token:
        return None, {"enabled": False, "reason": "missing_env"}
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/browser-rendering/content"
    try:
        async with httpx.AsyncClient(timeout=55) as client:
            r = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"url": root, "gotoOptions": {"waitUntil": "domcontentloaded", "timeout": 30000}, "actionTimeout": 45000},
            )
            data = r.json()
            if r.status_code != 200 or not data.get("success"):
                return None, {"enabled": True, "status": r.status_code, "error": str(data)[:300]}
            result = data.get("result")
            if isinstance(result, str):
                return result, {"enabled": True, "status": 200}
            if isinstance(result, dict):
                return str(result.get("content") or result.get("html") or ""), {"enabled": True, "status": 200}
            return "", {"enabled": True, "status": 200}
    except Exception as e:
        return None, {"enabled": True, "status": 0, "error": str(e)[:300]}


async def optional_browserless(root: str) -> Tuple[Optional[str], Dict[str, Any]]:
    enabled = os.getenv("BROWSERLESS_DIAGNOSTIC_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    endpoint = os.getenv("BROWSERLESS_CONTENT_URL", "").strip()
    if not enabled:
        return None, {"enabled": False, "reason": "disabled_by_default_or_scope"}
    if not endpoint:
        return None, {"enabled": False, "reason": "missing_env"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(endpoint, json={"url": root, "waitUntil": "domcontentloaded", "timeout": 45000})
            if r.status_code != 200:
                return None, {"enabled": True, "status": r.status_code, "error": r.text[:300]}
            return r.text, {"enabled": True, "status": 200}
    except Exception as e:
        return None, {"enabled": True, "status": 0, "error": str(e)[:300]}


async def direct_feed_probe(root: str, candidates: List[str], user_agent: str = "") -> Dict[str, Any]:
    tried = []
    seen = set()
    prioritized = []
    for candidate in candidates:
        u = urljoin(root + "/", candidate)
        if not same_host(u, root) or u in seen:
            continue
        seen.add(u)
        score = 0
        low = u.lower()
        if "woocommerce_gpf" in low or "woo_feed=" in low:
            score += 40
        if any(x in low for x in ("google", "merchant", "shopping")):
            score += 20
        if low.endswith(".xml") or ".xml?" in low:
            score += 10
        prioritized.append((score, u))
    prioritized = [u for _, u in sorted(prioritized, reverse=True)][:MAX_DIRECT_FEED_PROBES]
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WooCommerceV175FeedProbe/2026.09)",
        "Accept": "application/xml, application/rss+xml, text/xml, */*",
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
        for u in prioritized:
            try:
                r = await client.get(u)
                body = await r.aread()
                ok, count, sha = native_google_valid(body, r.headers.get("content-type", ""))
                tried.append({"url": u, "status": r.status_code, "final_url": str(r.url), "ct": r.headers.get("content-type", ""), "bytes": len(body), "native": ok})
                if ok and same_host(str(r.url), root):
                    return {"verified": True, "url": str(r.url), "item_count": count, "sha256": sha, "tried": tried[-30:]}
            except Exception as e:
                tried.append({"url": u, "status": 0, "error": str(e)[:180], "native": False})
    return {"verified": False, "url": None, "item_count": 0, "sha256": "", "tried": tried[-60:]}


async def ai_advisory(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Use the six configured external AI APIs as bounded advisory fallbacks.

    The advisory output can classify evidence or suggest candidate feed hypotheses.
    It never verifies a feed, bypasses access controls, or changes extraction authority.
    """
    provider_specs = [
        ("openrouter_free", "https://openrouter.ai/api/v1/chat/completions", "openrouter/free", "OPENROUTER"),
        ("groq", "https://api.groq.com/openai/v1/chat/completions", "openai/gpt-oss-120b", "GROQ"),
        ("gemini", "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini-3.8-flash", "GEMINI"),
        ("nvidia_nim", "https://integrate.api.nvidia.com/v1/chat/completions", "deepseek-ai/deepseek-v4.1-flash", "NVIDIA_NIM"),
        ("cohere_free", "https://api.cohere.ai/compatibility/v1/chat/completions", "command-a-plus-05-2026", "COHERE"),
        ("huggingface_free", "https://router.huggingface.co/v1/chat/completions", "openai/gpt-oss-120b", "HUGGINGFACE"),
    ]

    try:
        raw_config = json.loads(os.getenv("PROVIDER_KEYS_JSON", "{}") or "{}")
    except json.JSONDecodeError:
        raw_config = {}
    if not isinstance(raw_config, dict):
        raw_config = {}

    explicit_keys = {
        "nvidia_nim": os.getenv("NVIDIA_NIM_API_KEY", "").strip(),
        "cohere_free": os.getenv("COHERE_API_KEY", "").strip(),
        "huggingface_free": os.getenv("HF_TOKEN", "").strip(),
    }

    prompt = {
        "task": "Classify WooCommerce plugin evidence. Return JSON {family,confidence,why}. Advisory only; never invent verification.",
        "evidence": {
            "plugin_asset_slugs": evidence.get("plugin_asset_slugs", []),
            "namespaces": evidence.get("namespaces", []),
            "xhr_urls": evidence.get("xhr_urls", [])[:80],
            "http_api_namespaces": evidence.get("http_api_namespaces", []),
        },
    }

    outcomes: List[Dict[str, Any]] = []
    async with httpx.AsyncClient(timeout=25) as client:
        for provider, endpoint, default_model, config_name in provider_specs:
            config = raw_config.get(provider) if isinstance(raw_config.get(provider), dict) else {}
            key = explicit_keys.get(provider, str(config.get("api_key") or "").strip())
            if not key:
                outcomes.append({"provider": provider, "outcome": "unconfigured"})
                continue

            model = str(config.get("model") or default_model).strip() or default_model
            if provider in {"nvidia_nim", "cohere_free", "huggingface_free"}:
                model = default_model

            started = time.monotonic()
            try:
                r = await client.post(
                    endpoint,
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "temperature": 0,
                        "max_tokens": 256,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": "Return only JSON. Advisory classification only; never claim feed existence or successful web access."},
                            {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                        ],
                    },
                )
                latency_ms = max(0, int((time.monotonic() - started) * 1000))
                if r.status_code < 200 or r.status_code >= 300:
                    failure = "rate_limited" if r.status_code == 429 else "request_failed"
                    outcomes.append({"provider": provider, "outcome": failure, "status": r.status_code, "latency_ms": latency_ms})
                    continue

                body = r.json()
                content = body.get("choices", [{}])[0].get("message", {}).get("content", "{}")
                result = json.loads(content)
                outcomes.append({"provider": provider, "outcome": "success", "status": r.status_code, "latency_ms": latency_ms})
                return {
                    "enabled": True,
                    "provider": provider,
                    "model": model,
                    "status": r.status_code,
                    "latency_ms": latency_ms,
                    "result": result,
                    "outcomes": outcomes,
                }
            except Exception as exc:
                outcomes.append({
                    "provider": provider,
                    "outcome": "temporary",
                    "latency_ms": max(0, int((time.monotonic() - started) * 1000)),
                    "error": type(exc).__name__,
                })

    return {
        "enabled": bool(outcomes),
        "provider": None,
        "model": None,
        "status": None,
        "latency_ms": None,
        "result": {},
        "outcomes": outcomes,
        "reason": "all_active_ai_providers_unavailable",
    }




# Backward-compatible name for existing callers/tests.
groq_advisory = ai_advisory


async def passive_public_discovery(root: str) -> Dict[str, Any]:
    if not PASSIVE_INDEX_ENABLED:
        return {"enabled": False, "urls": [], "historical": [], "errors": []}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WooCommerceV175PassiveDiscovery/2026.09)", "Accept": "text/plain, application/xml, */*"}
    urls = set()
    historical = set()
    blobs = []
    errors = []
    probes = [
        "/robots.txt", "/wp-sitemap.xml", "/wp-sitemap.xml.gz", "/sitemap.xml", "/sitemap_index.xml",
        "/product-sitemap.xml", "/product-sitemap1.xml",
    ]
    directory_urls = set()
    directory_reports = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for path in probes:
            u = urljoin(root + "/", path)
            try:
                r = await client.get(u)
                body = await r.aread()
                if r.status_code == 200:
                    txt = body.decode("utf-8", "ignore")[:600_000]
                    blobs.append(txt)
                    urls.update(discover_urls_from_xml_or_text(txt, root))
                    urls.update(passive_sitemap_candidates(txt, root))
            except Exception as e:
                errors.append({"url": u, "error": str(e)[:180]})

        # Public directory indexes are an important recovery path for plugins whose feed
        # filename is generated/randomized (e.g. CTX Feed and Product Feed PRO).
        async def inspect_directory(directory: str):
            u = urljoin(root + "/", directory.lstrip("/"))
            try:
                r = await client.get(u, timeout=8)
                body = await r.aread()
                text = body.decode("utf-8", "ignore")[:250_000]
                candidates = public_directory_feed_candidates(text, root, directory) if r.status_code == 200 else []
                return {
                    "directory": directory,
                    "status": r.status_code,
                    "candidate_urls": candidates,
                }
            except Exception as e:
                return {"directory": directory, "status": 0, "candidate_urls": [], "error": str(e)[:180]}

        directory_results = await asyncio.gather(*(inspect_directory(d) for d in PLUGIN_FEED_DIRECTORIES))
        for report in directory_results:
            directory_reports.append(report)
            directory_urls.update(report.get("candidate_urls") or [])
            urls.update(report.get("candidate_urls") or [])
        if WAYBACK_ENABLED:
            try:
                pattern = quote(bare_host(root) + "/*", safe="")
                filter_expr = quote(".*(feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed).*", safe="")
                api = f"https://web.archive.org/cdx/search/cdx?url={pattern}&output=json&fl=original,statuscode,mimetype&filter=statuscode:200&filter=urlkey:{filter_expr}&collapse=urlkey&limit=80"
                r = await client.get(api, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    rows = data[1:] if isinstance(data, list) and data and isinstance(data[0], list) else data
                    for row in rows or []:
                        if isinstance(row, list) and row:
                            u = str(row[0])
                            if same_host(u, root):
                                historical.add(u)
            except Exception as e:
                errors.append({"source": "wayback", "error": str(e)[:180]})
        if COMMONCRAWL_ENABLED:
            try:
                idx = await client.get("https://index.commoncrawl.org/collinfo.json", timeout=20)
                if idx.status_code == 200:
                    coll = idx.json()
                    index_id = str(coll[0].get("id")) if coll else ""
                    if index_id:
                        pattern = quote(bare_host(root) + "/*", safe="")
                        api = f"https://index.commoncrawl.org/{index_id}-index?url={pattern}&output=json&matchType=prefix&filter=status:200&filter=url:feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed&limit=80"
                        cr = await client.get(api, timeout=25)
                        if cr.status_code == 200:
                            for line in cr.text.splitlines():
                                try:
                                    row = json.loads(line)
                                    u = str(row.get("url", ""))
                                    if same_host(u, root):
                                        historical.add(u)
                                except Exception:
                                    continue
            except Exception as e:
                errors.append({"source": "commoncrawl", "error": str(e)[:180]})
    return {
        "enabled": True,
        "urls": sorted(urls)[:300],
        "historical": sorted(historical)[:300],
        "blobs": blobs[:20],
        "errors": errors,
        "directory_candidates": sorted(directory_urls)[:240],
        "directory_reports": directory_reports[:20],
    }


async def probe_site(name: str, root: str) -> Dict[str, Any]:
    start_time = time.time()
    host = bare_host(root)
    if host in KNOWN_10:
        raise RuntimeError(f"known-site exclusion violated for target: {host}")

    source_blobs: List[str] = []
    all_requests: List[str] = []
    all_slugs: List[str] = []
    all_namespaces: List[str] = []
    browser_results: List[Dict[str, Any]] = []

    # Clean standard browser passes only. Browser state is never carried between engines.
    for engine in ("chromium", "firefox", "webkit"):
        be, _, html, response_blobs = await browser_engine(root, engine)
        browser_results.append(asdict(be))
        if not be.challenge:
            source_blobs.append(html)
            source_blobs.extend(response_blobs)
        all_requests.extend(be.xhr_urls)
        all_requests.extend(be.resource_urls)
        # Plugin slugs remain diagnostic even when a challenge is present; they never make a blocked site admissible.
        all_slugs.extend(be.plugin_asset_slugs)
        all_namespaces.extend(be.namespaces)

    challenge_encountered = any(bool(b.get("challenge_encountered")) for b in browser_results)
    clean_browser_success = any(int(b.get("status") or 0) == 200 and not b.get("challenge") for b in browser_results)

    cf_html, cf_meta = await optional_cf_content(root)
    bl_html, bl_meta = await optional_browserless(root)
    if cf_html:
        all_slugs.extend(parse_plugin_slugs(cf_html))
        all_namespaces.extend(parse_namespaces(cf_html))
    if bl_html:
        all_slugs.extend(parse_plugin_slugs(bl_html))
        all_namespaces.extend(parse_namespaces(bl_html))

    # Direct public fetch is deliberately cookie-free.
    direct_home = ""
    direct_ua = "Mozilla/5.0 (compatible; WooCommerceV175PluginRecovery/2026.09)"
    try:
        headers = {"User-Agent": direct_ua, "Accept": "text/html,application/xhtml+xml,*/*;q=.8"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20) as client:
            r = await client.get(root)
            body = await r.aread()
            direct_home = body.decode("utf-8", "ignore")[:2_000_000]
            if r.status_code == 200 and not is_challenge(r.status_code, direct_home):
                source_blobs.append(direct_home)
            if is_challenge(r.status_code, direct_home):
                challenge_encountered = True
    except Exception:
        pass

    # Public API surface without browser cookies / clearance state.
    api_evidence: List[ApiEvidence] = []
    try:
        api_evidence, api_blobs, api_ns = await api_surface(root, direct_ua)
        source_blobs.extend(api_blobs)
        all_namespaces.extend(api_ns)
    except Exception:
        pass

    passive = await passive_public_discovery(root)
    source_blobs.extend(passive.get("blobs") or [])
    all_requests.extend(passive.get("urls") or [])
    historical = passive.get("historical") or []

    all_slugs = sorted(set(all_slugs))
    all_namespaces = sorted(set(all_namespaces))
    all_requests = sorted(set(x for x in all_requests if same_host(x, root)))[:500]
    hits = find_plugin_hits(source_blobs + all_requests, all_slugs, all_namespaces)
    family = "unknown_woocommerce"
    family_confidence = "low"
    if hits:
        family = sorted(hits, key=lambda k: (-len(hits[k]), k))[0]
        family_confidence = plugin_family_confidence(hits, all_slugs, all_namespaces)

    explicit = explicit_xml_candidates("\n".join(source_blobs + all_requests), root)
    explicit_feed_candidates = filter_explicit_feed_candidates(explicit)
    query_candidates = query_feed_candidates("\n".join(source_blobs + all_requests), root)
    candidates = list(dict.fromkeys(
        explicit_feed_candidates
        + query_candidates
        + passive.get("urls", [])
        + passive.get("directory_candidates", [])
        + historical
    ))
    candidates.extend(GENERIC_FEED_PATHS)
    if family in PLUGIN_CANDIDATES:
        candidates = PLUGIN_CANDIDATES[family] + candidates
    candidates = list(dict.fromkeys(candidates))

    api_integrated_google = family == "google_for_woocommerce" and not explicit_feed_candidates and not query_candidates
    if api_integrated_google:
        feed = {
            "verified": False,
            "url": None,
            "item_count": 0,
            "sha256": "",
            "skipped": True,
            "skip_reason": "google_for_woocommerce_is_api_integrated; no standalone_xml_feed_expected_without_public_feed_url",
            "tried": [],
        }
    else:
        # A browser challenge on the homepage does not by itself invalidate an independently
        # public feed endpoint. Feed probing remains cookie-free, and only the current feed
        # payload itself can earn native-feed verification.
        feed = await direct_feed_probe(root, candidates, direct_ua)

    admissible = native_verification_admissible(
        challenge_encountered=challenge_encountered,
        clean_browser_success=clean_browser_success,
        native_feed_verified=bool(feed.get("verified")),
    )

    evidence = {
        "site": name,
        "url": root,
        "version": "V175-derived-plugin-harness-2026.09",
        "family": family,
        "family_confidence": family_confidence,
        "family_hits": hits,
        "plugin_asset_slugs": all_slugs,
        "namespaces": all_namespaces,
        "xhr_urls": all_requests,
        "api_evidence": [asdict(x) for x in api_evidence],
        "http_api_namespaces": sorted(set(x for a in api_evidence for x in a.namespaces)),
        "browser": browser_results,
        "challenge_encountered": challenge_encountered,
        "admissible_for_native_verification": admissible,
        "cloudflare": cf_meta,
        "browserless": bl_meta,
        "passive_discovery": {
            "enabled": passive.get("enabled"),
            "current_candidate_urls": passive.get("urls", [])[:200],
            "directory_candidates": passive.get("directory_candidates", [])[:200],
            "directory_reports": passive.get("directory_reports", [])[:20],
            "historical_candidate_urls": historical[:200],
            "errors": passive.get("errors", []),
        },
        "candidate_count": len(candidates),
        "explicit_candidates": explicit[:120],
        "explicit_feed_candidates": explicit_feed_candidates[:120],
        "query_feed_candidates": query_candidates[:120],
        "native_feed": feed,
        "feed_transport": "api_integrated" if api_integrated_google else "standalone_xml_candidate_probe",
        "elapsed_s": round(time.time() - start_time, 2),
    }
    evidence["ai_advisory"] = await ai_advisory(evidence)
    return evidence


async def main() -> int:
    shard = int(os.getenv("SHARD", "1"))
    shards = int(os.getenv("SHARDS", "6"))
    selected = [(n, u) for i, (n, u) in enumerate(TARGETS) if i % shards + 1 == shard]
    out_dir = Path("out") / "woocommerce-v175-plugin-recovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for name, root in selected:
        result = await probe_site(name, root)
        results.append(result)
        print(json.dumps({
            "site": result["site"],
            "family": result["family"],
            "native_verified": bool(result["native_feed"].get("verified")),
            "candidate_count": result["candidate_count"],
            "elapsed_s": result["elapsed_s"],
            "browser": [(b["engine"], b["status"], b["cf_clearance"]) for b in result["browser"]],
        }), flush=True)
    payload = {
        "schema": "woocommerce-v175-plugin-recovery/v1",
        "version": "V175-derived-plugin-harness-2026.09",
        "shard": shard,
        "shards": shards,
        "targets": [n for n, _ in selected],
        "results": results,
        "summary": {            "sites": len(results),
            "native_verified": sum(1 for x in results if x["native_feed"].get("verified")),
            "challenge_encountered": sum(1 for x in results if x.get("challenge_encountered")),            "admissible_for_native_verification": sum(1 for x in results if x.get("admissible_for_native_verification")),
            "plugin_groups": {
                k: sum(1 for x in results if x["family"] == k)
                for k in sorted(set(x["family"] for x in results))
            }
        }
    }
    (out_dir / f"shard-{shard}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

# v175-run-sync: latest workflow head dispatch