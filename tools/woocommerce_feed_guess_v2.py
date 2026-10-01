#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from typing import Iterable, List, Tuple
from urllib.parse import urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
BASE_PATH = ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py"

spec = importlib.util.spec_from_file_location("wc_v175_base_v2", BASE_PATH)
assert spec and spec.loader
BASE = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = BASE
spec.loader.exec_module(BASE)

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
    ("Cosmic Byte", "https://www.thecosmicbyte.com"),
    ("Meckeys", "https://www.meckeys.com"),
    ("StacksKB", "https://stackskb.com"),
    ("Theproaudio", "https://www.theproaudio.com"),
]

from tools import woocommerce_v175_discovery as DISCOVERY

DISCOVERY.PLUGIN_RULES = list(DISCOVERY.PLUGIN_RULES) + [
    ("rexfed_product_feed", ("best-woocommerce-feed", "rexfeed", "rex-wpfm", "rex_product_feed")),
    ("wpfactory_product_xml_feeds", (
        "product-xml-feeds-for-woocommerce",
        "alg_wc_product_xml_feeds",
        "alg_products_xml_file_path",
    )),
    ("svmpforge_product_feed", (
        "svmpforge-product-feed-for-woocommerce",
        "svmpforge",
        "apfw-feed",
    )),
]

DISCOVERY.PLUGIN_CANDIDATES = dict(DISCOVERY.PLUGIN_CANDIDATES)
DISCOVERY.PLUGIN_CANDIDATES.update({
    "rexfed_product_feed": [],
    "wpfactory_product_xml_feeds": ["/products.xml"],
    "svmpforge_product_feed": [],
})

DISCOVERY.PASSIVE_FEED_HINT_RE = re.compile(
    r"(?:feed|google|merchant|shopping|woocommerce_gpf|woo_feed|wppfm|wpfm|"
    r"webtoffee|adtribes|feedcraft|product-feed|apfw-feed|best-woocommerce-feed|"
    r"product-xml-feeds-for-woocommerce|alg_products_xml)",
    re.I,
)

def is_static_asset_url(url: str) -> bool:
    try:
        path = (urlsplit(url).path or "").lower()
    except Exception:
        return True
    bad_ext = (
        ".js", ".mjs", ".css", ".map", ".woff", ".woff2", ".ttf", ".otf",
        ".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".ico",
    )
    if path.endswith(bad_ext):
        return True
    for prefix in ("/wp-content/plugins/", "/wp-content/themes/", "/wp-includes/"):
        if prefix in path and not any(k in path for k in ("feed", "google", "merchant", "shopping", "xml")):
            return True
    return False

def filter_explicit_feed_candidates(urls: Iterable[str]) -> List[str]:
    out = set()
    for raw in urls:
        try:
            u = str(raw)
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        low = u.lower()
        if path.endswith("robots.txt") or "sitemap" in path or is_static_asset_url(u):
            continue
        if not (
            re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I)
            or BASE.PASSIVE_FEED_HINT_RE.search(u)
            or "woocommerce_gpf=" in low
            or "woo_feed=" in low
        ):
            continue
        out.add(u)
    return sorted(out)[:160]

def query_feed_candidates(text: str, root: str) -> List[str]:
    out = set()
    samples = []
    for raw in re.findall(r"https?://[^\s\"'<>]+", text or "", re.I):
        samples.append(raw.rstrip(",.;)"))
    for raw in re.findall(
        r'''(?:href|src|loc|data-href|data-url)=["']([^"']+)["']''',
        text or "",
        re.I,
    ):
        samples.append(raw)
    for raw in samples:
        try:
            u = urljoin(root + "/", raw)
            if not BASE.same_host(u, root) or is_static_asset_url(u):
                continue
            low = u.lower()
            if "woocommerce_gpf=" in low:
                out.add(u)
                value = dict(
                    part.split("=", 1)
                    for part in urlsplit(u).query.split("&")
                    if "=" in part
                ).get("woocommerce_gpf", "")
                if value.lower() == "google":
                    for start in (0, 100):
                        out.add(urljoin(
                            root + "/",
                            f"/?woocommerce_gpf=google&gpf_start={start}&gpf_limit=100",
                        ))
            elif "woo_feed=" in low:
                out.add(u)
        except Exception:
            continue
    return sorted(out)[:120]

def native_google_valid(body: bytes, content_type: str) -> Tuple[bool, int, str]:
    if not body:
        return False, 0, ""
    raw = body
    try:
        if raw[:2] == b"\x1f\x8b" or "gzip" in (content_type or "").lower():
            import gzip
            raw = gzip.decompress(raw)
    except Exception:
        return False, 0, ""
    text = raw.decode("utf-8", "ignore")
    low = text.lower()
    if not re.search(r"https?://base\.google\.com/ns/1\.0", low):
        return False, 0, ""
    if not re.search(r"<rss\b|<feed\b", low):
        return False, 0, ""
    if re.search(r"just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser", low):
        return False, 0, ""
    blocks = re.findall(r"<(?:item|entry)\b[^>]*>.*?</(?:item|entry)>", text, re.I | re.S)
    if not blocks:
        return False, 0, ""
    required = (
        r"<g:id\b[^>]*>.*?</g:id>",
        r"<g:title\b[^>]*>.*?</g:title>",
        r"<g:link\b[^>]*>.*?</g:link>",
        r"<g:price\b[^>]*>.*?</g:price>",
    )
    if not any(all(re.search(pattern, block, re.I | re.S) for pattern in required) for block in blocks):
        return False, 0, ""
    return True, len(blocks), hashlib.sha256(raw).hexdigest()

BASE.PLUGIN_RULES = DISCOVERY.PLUGIN_RULES
BASE.PLUGIN_CANDIDATES = DISCOVERY.PLUGIN_CANDIDATES
BASE.PASSIVE_FEED_HINT_RE = DISCOVERY.PASSIVE_FEED_HINT_RE
BASE.find_plugin_hits = DISCOVERY.find_plugin_hits
BASE.filter_explicit_feed_candidates = filter_explicit_feed_candidates
BASE.query_feed_candidates = query_feed_candidates
BASE.native_google_valid = native_google_valid

async def run_one(name: str, root: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            result = await BASE.probe_site(name, root)
        except Exception as exc:
            result = {
                "site": name,
                "url": root,
                "family": "probe_error",
                "family_confidence": "low",
                "candidate_count": 0,
                "browser": [],
                "passive_discovery": {},
                "native_feed": {"verified": False, "url": None, "item_count": 0, "sha256": "", "tried": []},
                "elapsed_s": 0,
                "probe_error": f"{type(exc).__name__}:{exc}",
            }
        result["guessing_stage"] = "v2_public_discovery"
        return result

async def main() -> int:
    shard = int(os.getenv("SHARD", "1"))
    shards = int(os.getenv("SHARDS", "6"))
    selected = [x for i, x in enumerate(TARGETS) if i % shards + 1 == shard]
    sem = asyncio.Semaphore(max(1, min(len(selected), int(os.getenv("SITE_CONCURRENCY", "2")))))
    results = list(await asyncio.gather(*(run_one(name, root, sem) for name, root in selected)))
    results.sort(key=lambda x: x["site"])
    out = ROOT / "out" / "woocommerce-guessing-v2"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "woocommerce-guessing-v2-public-discovery/v1",
        "shard": shard,
        "shards": shards,
        "targets": [n for n, _ in selected],
        "methods": [
            "current-browser-discovery",
            "current-http-api-discovery",
            "robots-sitemap-discovery",
            "wayback-discovery",
            "commoncrawl-discovery",
            "plugin-family-discovery",
            "bounded-documentation-candidates",
            "strict-native-merchant-validation",
        ],
        "security_boundary": {
            "public_only": True,
            "no_captcha_bypass": True,
            "no_clearance_cookie_replay": True,
            "no_authentication_bypass": True,
            "no_proxy_evasion": True,
            "no_random_token_enumeration": True,
        },
        "results": results,
    }
    (out / f"shard-{shard}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    for result in results:
        print(json.dumps({
            "site": result["site"],
            "family": result.get("family"),
            "confidence": result.get("family_confidence"),
            "native_verified": bool((result.get("native_feed") or {}).get("verified")),
            "candidate_count": result.get("candidate_count"),
            "elapsed_s": result.get("elapsed_s"),
            "probe_error": result.get("probe_error"),
        }), flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
