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
It preserves the V175 contracts while adding:
- Chromium + Firefox/Gecko + WebKit browser passes
- API replay using in-memory public browser cookies
- optional Cloudflare Browser Rendering API and Browserless content adapters
- plugin fingerprint normalization
- plugin-family grouping-ready JSON evidence
- plugin-specific native Google XML candidate generation
- strict payload validation
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
from urllib.parse import urljoin, urlsplit

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
    ("Moskeys", "https://moskeys.com"),
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
        "woo feed", "woo_feed-",
    )),
    ("adtribes_product_feed_pro", (
        "product feed pro", "adtribes", "woo-product-feed-pro",
        "product-feed-pro",
    )),
    ("wpfm_product_feed_manager", (
        "product feed manager", "wppfm", "wppfm-feeds", "wpfm/v1",
    )),
    ("webtoffee_product_feed", (
        "webtoffee", "webtoffee_product_feed", "webtoffee-product-feed",
    )),
    ("codesolz_merchant_feed_booster", (
        "codesolz", "codesolz-feeds", "merchant feed booster",
    )),
    ("feedcraft", (
        "feedcraft", "feedcraft-product-feed",
    )),
    ("google_for_woocommerce", (
        "google-listings-and-ads", "google for woocommerce",
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


@dataclass
class BrowserEvidence:
    engine: str
    status: int = 0
    challenge: bool = False
    cf_clearance: bool = False
    cookie_names: List[str] = None
    user_agent: str = ""
    html_len: int = 0
    plugin_asset_slugs: List[str] = None
    namespaces: List[str] = None
    xhr_urls: List[str] = None
    error: str = ""

    def __post_init__(self):
        self.cookie_names = self.cookie_names or []
        self.plugin_asset_slugs = self.plugin_asset_slugs or []
        self.namespaces = self.namespaces or []
        self.xhr_urls = self.xhr_urls or []


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


def parse_namespaces(text: str) -> List[str]:
    out = set()
    for m in re.finditer(r'"namespaces"\s*:\s*\[(.*?)\]', text or "", re.S):
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            out.add(item)
    for m in re.findall(r'"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', text or ""):
        if any(k in m.lower() for k in ("feed", "wpfm", "woo", "google", "merchant", "ctx")):
            out.add(m)
    return sorted(out)


def find_plugin_hits(blobs: Iterable[str], plugin_slugs: Iterable[str], namespaces: Iterable[str]) -> Dict[str, List[str]]:
    all_text = "\n".join(str(x or "") for x in blobs).lower()
    evidence = set(str(x).lower() for x in plugin_slugs)
    evidence.update(str(x).lower() for x in namespaces)
    hits: Dict[str, List[str]] = {}
    for family, needles in PLUGIN_RULES:
        family_hits = []
        for n in needles:
            if n in all_text:
                family_hits.append(n)
        for e in evidence:
            for n in needles:
                if n in e:
                    family_hits.append(e)
                    break
        if family_hits:
            hits[family] = sorted(set(family_hits))[:20]
    return hits


def explicit_xml_candidates(text: str, root: str) -> List[str]:
    out = set()
    for raw in re.findall(r'https?://[^\s"\'<>]+', text or "", re.I):
        u = raw.rstrip("),.;")
        if same_host(u, root) and re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I):
            out.add(u)
    for raw in re.findall(r'(?:href|src|loc)=["\']([^"\']+)["\']', text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I):
            out.add(u)
    for raw in re.findall(r'(?i)(?:woo_feed|woocommerce_gpf|wppfm|feedcraft)[^"\'<>\s&]*', text or ""):
        if raw.startswith("http"):
            out.add(raw.rstrip("),.;"))
    return sorted(out)[:100]


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
    count = len(re.findall(r"<item\b", text, re.I))
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


async def api_surface(root: str, cookies: Dict[str, str]) -> Tuple[List[ApiEvidence], List[str], List[str]]:
    ua = cookies.pop("__ua__", "") if "__ua__" in cookies else ""
    headers = {
        "User-Agent": ua or "Mozilla/5.0 (compatible; WooCommerceV175PluginRecovery/2026.09)",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }
    api_out: List[ApiEvidence] = []
    blobs: List[str] = []
    ns: List[str] = []
    async with httpx.AsyncClient(headers=headers) as client:
        for path in API_PATHS:
            url = urljoin(root + "/", path)
            st, final, hdrs, body = await http_get(client, url, dict(cookies), 30)
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
            st, final, hdrs = await http_options(client, url, dict(cookies), 15)
            api_out.append(ApiEvidence(
                url=url, status=st, allow=hdrs.get("allow", ""),
                content_type=hdrs.get("content-type", ""), body_read=False
            ))
    return api_out, blobs, sorted(set(ns))


async def browser_engine(root: str, engine: str, seed_cookies: Optional[Dict[str, str]] = None):
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
            if seed_cookies:
                try:
                    await context.add_cookies([
                        {"name": k, "value": str(v), "domain": bare_host(root), "path": "/"}
                        for k, v in seed_cookies.items() if k and v
                    ])
                except Exception:
                    pass
            page = await context.new_page()
            xhr: List[str] = []
            response_blobs: List[str] = []

            async def on_response(resp):
                try:
                    u = resp.url
                    hdrs = await resp.all_headers()
                    ct = hdrs.get("content-type", "")
                    if not same_host(u, root):
                        return
                    interesting = (
                        "json" in ct.lower() or "xml" in ct.lower()
                        or any(x in u.lower() for x in (
                            "wp-json", "product", "catalog", "search", "feed",
                            "google", "merchant", "ctx", "wpfm", "webtoffee",
                            "adtribes", "woo-feed", "feedcraft", "/api/",
                        ))
                    )
                    if not interesting:
                        return
                    xhr.append(u)
                    if ("json" in ct.lower() or "xml" in ct.lower()) and len(response_blobs) < 25:
                        try:
                            b = await resp.body()
                            if 0 < len(b) <= 250_000:
                                response_blobs.append(b.decode("utf-8", "ignore"))
                        except Exception:
                            pass
                except Exception:
                    pass

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
            title = ""
            try:
                title = await page.title()
            except Exception:
                pass
            cookies = await context.cookies()
            cookie_names = sorted({str(c.get("name")) for c in cookies if c.get("name")})
            cookie_values = {str(c["name"]): str(c.get("value") or "") for c in cookies if c.get("name")}
            ua = ""
            try:
                ua = await page.evaluate("navigator.userAgent")
            except Exception:
                pass
            await browser.close()
            slugs = parse_plugin_slugs(html + "\n" + "\n".join(xhr) + "\n" + "\n".join(response_blobs))
            namespaces = parse_namespaces(html + "\n" + "\n".join(response_blobs))
            return BrowserEvidence(
                engine=engine,
                status=getattr(resp, "status", 0) if resp else 0,
                challenge=is_challenge(getattr(resp, "status", 0) if resp else 0, html),
                cf_clearance=("cf_clearance" in cookie_values or "__cf_bm" in cookie_values),
                cookie_names=cookie_names,
                user_agent=ua,
                html_len=len(html),
                plugin_asset_slugs=slugs,
                namespaces=namespaces,
                xhr_urls=sorted(set(xhr))[:200],
                error="",
            ), cookie_values, html, response_blobs
    except Exception as e:
        return BrowserEvidence(engine=engine, error=str(e)), {}, "", []


async def optional_cf_content(root: str) -> Tuple[Optional[str], Dict[str, Any]]:
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
    endpoint = os.getenv("BROWSERLESS_CONTENT_URL", "").strip()
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


async def direct_feed_probe(root: str, candidates: List[str], cookie_jars: List[Dict[str, str]]) -> Dict[str, Any]:
    tried = []
    seen = set()
    for candidate in candidates[:140]:
        u = urljoin(root + "/", candidate)
        if not same_host(u, root) or u in seen:
            continue
        seen.add(u)
        for cookies in cookie_jars[:5]:
            clean = {k: v for k, v in cookies.items() if k != "__ua__"}
            headers = {
                "User-Agent": cookies.get("__ua__") or "Mozilla/5.0 (compatible; WooCommerceV175FeedProbe/2026.09)",
                "Accept": "application/xml, application/rss+xml, text/xml, */*",
            }
            try:
                async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=45) as client:
                    r = await client.get(u, cookies=clean)
                    body = await r.aread()
                    ok, count, sha = native_google_valid(body, r.headers.get("content-type", ""))
                    tried.append({"url": u, "status": r.status_code, "ct": r.headers.get("content-type", ""), "bytes": len(body), "native": ok})
                    if ok and same_host(str(r.url), root):
                        return {
                            "verified": True,
                            "url": str(r.url),
                            "item_count": count,
                            "sha256": sha,
                            "tried": tried[-30:],
                        }
            except Exception as e:
                tried.append({"url": u, "status": 0, "error": str(e)[:180], "native": False})
    return {"verified": False, "url": None, "item_count": 0, "sha256": "", "tried": tried[-60:]}


async def groq_advisory(evidence: Dict[str, Any]) -> Dict[str, Any]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        return {"enabled": False, "reason": "missing_env"}
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    prompt = {
        "task": "Classify WooCommerce plugin evidence for one site. Do not invent. Return JSON {family,confidence,why}.",
        "evidence": {
            "plugin_asset_slugs": evidence.get("plugin_asset_slugs", []),
            "namespaces": evidence.get("namespaces", []),
            "xhr_urls": evidence.get("xhr_urls", [])[:80],
            "http_api_namespaces": evidence.get("http_api_namespaces", []),
        }
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={
                    "model": model,
                    "temperature": 0,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": "Return only JSON; advisory classification, never claim feed existence."},
                        {"role": "user", "content": json.dumps(prompt, ensure_ascii=False)},
                    ],
                },
            )
            if r.status_code != 200:
                return {"enabled": True, "status": r.status_code, "error": r.text[:300]}
            content = r.json().get("choices", [{}])[0].get("message", {}).get("content", "{}")
            return {"enabled": True, "status": 200, "result": json.loads(content)}
    except Exception as e:
        return {"enabled": True, "status": 0, "error": str(e)[:300]}


async def probe_site(name: str, root: str) -> Dict[str, Any]:
    start = time.time()
    host = bare_host(root)
    if host in KNOWN_10:
        raise RuntimeError(f"known-site exclusion violated for target: {host}")

    source_blobs: List[str] = []
    all_xhr: List[str] = []
    all_slugs: List[str] = []
    all_namespaces: List[str] = []
    browser_results: List[Dict[str, Any]] = []
    cookie_jars: List[Dict[str, str]] = []

    seed: Dict[str, str] = {}
    for engine in ("chromium", "firefox", "webkit"):
        be, cookies, html, response_blobs = await browser_engine(root, engine, seed)
        browser_results.append(asdict(be))
        source_blobs.append(html)
        source_blobs.extend(response_blobs)
        all_xhr.extend(be.xhr_urls)
        all_slugs.extend(be.plugin_asset_slugs)
        all_namespaces.extend(be.namespaces)
        if cookies:
            cookies["__ua__"] = be.user_agent
            cookie_jars.append(dict(cookies))
            seed = {k: v for k, v in cookies.items() if k != "__ua__"}

    cf_html, cf_meta = await optional_cf_content(root)
    bl_html, bl_meta = await optional_browserless(root)
    for x in (cf_html, bl_html):
        if x:
            source_blobs.append(x)
            all_slugs.extend(parse_plugin_slugs(x))
            all_namespaces.extend(parse_namespaces(x))

    direct_home = ""
    direct_cookies = dict(seed)
    direct_cookies.pop("__ua__", None)
    try:
        headers = {"User-Agent": seed.get("__ua__", "Mozilla/5.0"), "Accept": "text/html,application/xhtml+xml,*/*;q=.8"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
            r = await client.get(root, cookies=direct_cookies)
            direct_home = (await r.aread()).decode("utf-8", "ignore")[:2_000_000]
            source_blobs.append(direct_home)
    except Exception:
        pass

    api_evidence: List[ApiEvidence] = []
    try:
        api_cookies = dict(seed)
        api_cookies["__ua__"] = seed.get("__ua__", "Mozilla/5.0")
        api_evidence, api_blobs, api_ns = await api_surface(root, api_cookies)
        source_blobs.extend(api_blobs)
        all_namespaces.extend(api_ns)
    except Exception:
        pass

    all_slugs = sorted(set(all_slugs))
    all_namespaces = sorted(set(all_namespaces))
    all_xhr = sorted(set(x for x in all_xhr if same_host(x, root)))[:300]

    hits = find_plugin_hits(source_blobs + all_xhr, all_slugs, all_namespaces)
    family = "unknown_woocommerce"
    family_confidence = "low"
    if hits:
        family = sorted(hits, key=lambda k: (-len(hits[k]), k))[0]
        family_confidence = "high"

    explicit = explicit_xml_candidates("\n".join(source_blobs + all_xhr), root)
    candidates = list(explicit)
    candidates.extend(GENERIC_FEED_PATHS)
    if family in PLUGIN_CANDIDATES:
        candidates = PLUGIN_CANDIDATES[family] + candidates
    if family == "google_for_woocommerce" and not explicit:
        candidates = []

    for path in (
        "/wp-content/uploads/woo-feed/google/xml/",
        "/wp-content/uploads/woo-product-feed-pro/xml/",
        "/wp-content/uploads/wppfm-feeds/",
        "/wp-content/uploads/webtoffee_product_feed/",
        "/wp-content/uploads/codesolz-feeds/",
        "/feeds/",
        "/feed/",
    ):
        for jar in cookie_jars[:3]:
            clean = {k: v for k, v in jar.items() if k != "__ua__"}
            headers = {"User-Agent": jar.get("__ua__") or "Mozilla/5.0", "Accept": "text/html,*/*;q=.5"}
            try:
                async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=12) as client:
                    r = await client.get(urljoin(root + "/", path), cookies=clean)
                    txt = (await r.aread()).decode("utf-8", "ignore")[:250_000]
                    if r.status_code == 200:
                        candidates.extend(explicit_xml_candidates(txt, root))
            except Exception:
                pass

    candidates = list(dict.fromkeys(candidates))
    feed = await direct_feed_probe(root, candidates, cookie_jars or [{"__ua__": "Mozilla/5.0"}])

    evidence = {
        "site": name,
        "url": root,
        "version": "V175-derived-plugin-harness-2026.09",
        "family": family,
        "family_confidence": family_confidence,
        "family_hits": hits,
        "plugin_asset_slugs": all_slugs,
        "namespaces": all_namespaces,
        "xhr_urls": all_xhr,
        "api_evidence": [asdict(x) for x in api_evidence],
        "http_api_namespaces": sorted(set(x for a in api_evidence for x in a.namespaces)),
        "browser": browser_results,
        "cloudflare": cf_meta,
        "browserless": bl_meta,
        "candidate_count": len(candidates),
        "explicit_candidates": explicit[:100],
        "native_feed": feed,
        "elapsed_s": round(time.time() - start, 2),
    }
    evidence["groq_advisory"] = await groq_advisory(evidence)
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
        "summary": {
            "sites": len(results),
            "native_verified": sum(1 for x in results if x["native_feed"].get("verified")),
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
