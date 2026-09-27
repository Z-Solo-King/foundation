#!/usr/bin/env python3
"""Native-only WooCommerce Google Merchant XML URL discovery.

The program never constructs or emits a replacement product feed. It only
returns URLs that were fetched successfully and whose live XML payload passed
the strict Google Merchant product-feed classifier.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

UA = "Mozilla/5.0 (compatible; WooCommerceNativeGoogleFeedHunt/2026.09)"
ACCEPT = "application/xml, application/rss+xml, text/xml, text/plain;q=0.9, */*;q=0.1"
GOOGLE_NS = "http://base.google.com/ns/1.0"
ITEM_TAGS = {"item", "entry"}
SITEMAP_ROOTS = {"urlset", "sitemapindex"}
BLOCK_MARKERS = (
    "just a moment", "cf-chl-", "cf-turnstile", "captcha",
    "access denied", "attention required", "checking your browser",
)
PLUGIN_MARKERS = {
    "woocommerce_gpf": ("woocommerce_gpf", "woocommerce-google-product-feed"),
    "ctx_feed": ("ctx feed", "woo-feed"),
    "product_feed_pro": ("woo-product-feed-pro", "adtibes", "product feed pro"),
    "wppfm": ("wppfm-feeds", "product feed manager"),
    "feedcraft": ("feedcraft-product-feed",),
    "codesolz": ("codesolz-feeds",),
}

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
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-content-feed/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/google.xml",
    "/google-feed.xml",
    "/google_feed.xml",
    "/google-products.xml",
    "/google-product-feed.xml",
    "/google-shopping.xml",
    "/google-shopping-feed.xml",
    "/google-merchant.xml",
    "/google-merchant-feed.xml",
    "/merchant.xml",
    "/merchant-feed.xml",
    "/product-feed.xml",
    "/feed/google.xml",
    "/feeds/google.xml",
)

SLOW_PATHS = (
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=2500",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=5000",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=2500",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=5000",
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/google",
    "/wp-json/feedcraft-product-feed/v1/feed.xml",
    "/wp-json/feed-products/v1/google.xml",
    "/wp-json/google-product-feed/v1/xml",
    "/wp-json/google-feed/v1/xml",
    "/wp-json/woo-feed/v1/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google.xml",
    "/wp-content/uploads/woo-feed/google-feed.xml",
    "/google-shopping-products.xml",
    "/google-shopping-products-feed.xml",
    "/google-product-feed.xml?format=xml",
    "/feeds/google-product-feed.xml",
    "/feeds/google-products.xml",
    "/feeds/google-shopping-feed.xml",
    "/feed/google-feed.xml",
    "/feed/google-products.xml",
    "/feed/google-product-feed.xml",
    "/feed/google-shopping.xml",
    "/feed/google-shopping-feed.xml",
)

DIRECTORIES = (
    "/wp-content/uploads/woo-feed/google/xml/",
    "/wp-content/uploads/woo-feed/google/",
    "/wp-content/uploads/woo-feed/",
    "/wp-content/uploads/woo-product-feed-pro/xml/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/codesolz-feeds/",
    "/feeds/",
    "/feed/",
)

DISCOVERY_PATHS = (
    "/",
    "/robots.txt",
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/wp-sitemap.xml",
    "/wp-json/",
)

@dataclass(frozen=True)
class FetchResult:
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


def as_url(root: str, value: str) -> str | None:
    try:
        if value.startswith("/"):
            url = urllib.parse.urljoin(root.rstrip("/") + "/", value)
        elif value.startswith("http://") or value.startswith("https://"):
            url = value
        else:
            return None
        return url if same_host(url, root) else None
    except ValueError:
        return None


def fetch(url: str, timeout: float) -> FetchResult:
    started = time.monotonic()
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": ACCEPT,
            "Accept-Language": "en-IN,en;q=0.9",
            "Accept-Encoding": "gzip",
            "Cache-Control": "no-cache",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            data = response.read(32 * 1024 * 1024 + 1)
            if len(data) > 32 * 1024 * 1024:
                return FetchResult(url, response.geturl(), int(response.status), response.headers.get("content-type", ""), b"", int((time.monotonic()-started)*1000), "body_too_large")
            if response.headers.get("content-encoding", "").lower() == "gzip":
                data = gzip.decompress(data)
            return FetchResult(
                url, response.geturl(), int(response.status),
                response.headers.get("content-type", ""),
                data, int((time.monotonic()-started)*1000),
            )
    except urllib.error.HTTPError as exc:
        try:
            body = exc.read(256 * 1024)
        except OSError:
            body = b""
        return FetchResult(url, str(getattr(exc, "url", url)), int(exc.code), exc.headers.get("content-type", ""), body, int((time.monotonic()-started)*1000), "http_error")
    except Exception as exc:
        return FetchResult(url, url, 0, "", b"", int((time.monotonic()-started)*1000), type(exc).__name__)


def _local(tag: object) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def validate_google_xml(body: bytes, content_type: str) -> Validation:
    if not body:
        return Validation(False, "empty", 0, 0, ("empty_body",))
    raw = body
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError:
            return Validation(False, "gzip_invalid", 0, 0, ("gzip_parse_error",))
    text = raw[:32 * 1024 * 1024].decode("utf-8", "replace")
    stripped = text.lstrip("\ufeff \r\n\t")
    if not stripped.startswith(("<?xml", "<rss", "<feed", "<channel")):
        return Validation(False, "non_xml", 0, 0, ("not_xml_looking",))
    lower = stripped.lower()
    if any(marker in lower[:12000] for marker in BLOCK_MARKERS):
        return Validation(False, "blocked", 0, 0, ("challenge_or_access_denied",))
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return Validation(False, "invalid_xml", 0, 0, ("xml_parse_error",))
    root_name = _local(root.tag)
    if root_name in SITEMAP_ROOTS:
        return Validation(False, "sitemap", 0, 0, ("sitemap_excluded",))
    items = [n for n in root.iter() if _local(n.tag) in ITEM_TAGS]
    ns_fields = {
        _local(n.tag)
        for n in root.iter()
        if isinstance(n.tag, str) and n.tag.startswith("{"+GOOGLE_NS+"}")
    }
    valid_items = 0
    required = {"id", "title", "link", "price"}
    for item in items:
        fields = {
            _local(n.tag)
            for n in item.iter()
            if isinstance(n.tag, str) and n.tag.startswith("{"+GOOGLE_NS+"}")
        }
        if required.issubset(fields):
            valid_items += 1
    google_fields = len(ns_fields)
    if not valid_items:
        return Validation(False, "rss_or_atom", len(items), google_fields, (
            f"root={root_name}", f"items={len(items)}",
            "no_item_with_core_google_fields",
        ))
    return Validation(
        True,
        "rss_or_atom" if root_name in {"rss", "feed", "channel"} else "xml",
        len(items),
        google_fields,
        (f"root={root_name}", f"items={len(items)}", f"valid_items={valid_items}", f"google_fields={google_fields}"),
        hashlib.sha256(raw).hexdigest(),
    )


def extract_candidate_urls(text: str, root: str) -> tuple[str, ...]:
    decoded = html.unescape(text)
    candidates: set[str] = set()
    patterns = (
        r"https?://[^\s<>'\"\]\[)]+",
        r"""(?:href|src|url|feedUrl|feed_url|feedURL|product_feed|google_feed)\s*[:=]\s*['\"]([^'\"]+)['\"]""",
    )
    for pattern in patterns:
        for match in re.finditer(pattern, decoded, re.I):
            raw = match.group(1) if match.lastindex else match.group(0)
            raw = raw.rstrip(".,);")
            if not re.search(r"(?:\.xml(?:\.gz)?)(?:[?#].*)?$|feed|merchant|shopping|woocommerce_gpf", raw, re.I):
                continue
            value = as_url(root, raw)
            if value:
                candidates.add(value)
    return tuple(sorted(candidates))


def extract_wp_routes(text: str, root: str) -> tuple[str, ...]:
    if "wp-json" not in text.lower():
        return ()
    out: set[str] = set()
    for match in re.finditer(r'"(/wp-json/[^"]*(?:feed|google|merchant|product)[^"]*)"', text, re.I):
        value = as_url(root, html.unescape(match.group(1)))
        if value:
            out.add(value)
    return tuple(sorted(out))


def directory_candidates(text: str, root: str, directory: str) -> tuple[str, ...]:
    out: set[str] = set()
    decoded = html.unescape(text)
    for match in re.finditer(r'href=["\']([^"\']+)["\']', decoded, re.I):
        value = as_url(root, urllib.parse.urljoin(root.rstrip("/") + "/", match.group(1)))
        if value and urllib.parse.urlsplit(value).path.lower().endswith((".xml", ".xml.gz")):
            out.add(value)
    for match in re.finditer(r"https?://[^\s<>'\"\]\[)]+\.(?:xml|xml\.gz)(?:[?#][^\s<>'\"\]\[)]*)?", decoded, re.I):
        value = as_url(root, match.group(0).rstrip(".,);"))
        if value:
            out.add(value)
    return tuple(sorted(out))


def site_candidates(root: str) -> tuple[str, ...]:
    base = root.rstrip("/")
    urls = [urllib.parse.urljoin(base + "/", path.lstrip("/")) for path in (*FAST_PATHS, *SLOW_PATHS)]
    return tuple(dict.fromkeys(urls))


def choose_status(records: list[dict[str, object]], verified: str | None) -> str:
    if verified:
        return "verified_native"
    statuses = [int(r.get("status") or 0) for r in records]
    if any(s in {401, 403, 429} for s in statuses):
        return "transport_blocked"
    if any(s == 404 for s in statuses) and not any(s == 0 for s in statuses):
        return "candidate_negative_or_unverified"
    return "unverified"


def probe_site(site: str, root: str, *, max_workers: int = 8) -> SiteResult:
    started = time.monotonic()
    discovery: list[FetchResult] = []
    feed_records: list[dict[str, object]] = []
    discovered_urls: set[str] = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch, urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 15.0): p for p in DISCOVERY_PATHS}
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            discovery.append(result)
            if result.status == 200 and result.body:
                text = result.body.decode("utf-8", "replace")
                discovered_urls.update(extract_candidate_urls(text, root))
                discovered_urls.update(extract_wp_routes(text, root))

    marker_text = "\n".join(r.body.decode("utf-8", "replace")[:120000] for r in discovery if r.status == 200 and r.body)
    marker_text_lower = marker_text.lower()
    directories = list(DIRECTORIES)
    if "woocommerce_gpf" in marker_text_lower:
        # On-demand GPF feeds are dynamic and benefit from the long timeout.
        pass
    if any(k in marker_text_lower for k in PLUGIN_MARKERS["ctx_feed"]):
        directories.insert(0, "/wp-content/uploads/woo-feed/google/xml/")
    if any(k in marker_text_lower for k in PLUGIN_MARKERS["product_feed_pro"]):
        directories.insert(0, "/wp-content/uploads/woo-product-feed-pro/xml/")
    if any(k in marker_text_lower for k in PLUGIN_MARKERS["wppfm"]):
        directories.insert(0, "/wp-content/uploads/wppfm-feeds/")
    if any(k in marker_text_lower for k in PLUGIN_MARKERS["codesolz"]):
        directories.insert(0, "/wp-content/uploads/codesolz-feeds/")

    # Probe high-confidence URLs in parallel with a normal timeout.
    fast_urls = list(dict.fromkeys(
        urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/"))
        for p in FAST_PATHS
    ))
    slow_urls = list(dict.fromkeys(
        urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/"))
        for p in SLOW_PATHS
    ))

    def run_batch(urls: list[str], timeout: float, cap: int) -> str | None:
        nonlocal feed_records
        selected = urls[:cap]
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_map = {pool.submit(fetch, u, timeout): u for u in selected}
            for future in concurrent.futures.as_completed(future_map):
                result = future.result()
                record = {
                    "url": result.requested_url,
                    "final_url": result.final_url,
                    "status": result.status,
                    "content_type": result.content_type,
                    "elapsed_ms": result.elapsed_ms,
                    "error": result.error,
                }
                validation = validate_google_xml(result.body, result.content_type) if result.status == 200 else Validation(False, "not_checked", 0, 0, ())
                record["validation"] = asdict(validation)
                feed_records.append(record)
                if result.status == 200 and validation.valid and same_host(result.final_url, root):
                    return result.final_url
        return None

    verified = run_batch(fast_urls, 20.0, len(fast_urls))
    if verified is None:
        # Long-tail/dynamic feeds: deliberately separate slow lane because some
        # WooCommerce GPF implementations can take close to a minute.
        verified = run_batch(slow_urls, 95.0, len(slow_urls))

    # Publicly exposed directory indexes and page/robots/sitemap references.
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(directories))) as pool:
        directory_results = list(pool.map(
            lambda p: (p, fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 12.0)),
            list(dict.fromkeys(directories)),
        ))
    for directory, result in directory_results:
        if result.status == 200 and result.body:
            found = directory_candidates(result.body.decode("utf-8", "replace"), root, directory)
            discovered_urls.update(found)

    if verified is None and discovered_urls:
        discovered = [
            u for u in sorted(discovered_urls)
            if urllib.parse.urlsplit(u).path.lower().endswith((".xml", ".xml.gz"))
            or re.search(r"(feed|merchant|shopping|woocommerce_gpf)", u, re.I)
        ]
        verified = run_batch(discovered, 60.0, 120)

    if verified is None:
        # Retry only the explicit native GPF endpoint once with the maximum
        # timeout observed to be necessary in prior live testing.
        for p in ("/?woocommerce_gpf=google", "/woocommerce_gpf/google"):
            result = fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 110.0)
            validation = validate_google_xml(result.body, result.content_type) if result.status == 200 else Validation(False, "not_checked", 0, 0, ())
            feed_records.append({
                "url": result.requested_url, "final_url": result.final_url,
                "status": result.status, "content_type": result.content_type,
                "elapsed_ms": result.elapsed_ms, "error": result.error,
                "validation": asdict(validation),
                "retry": "slow_gpf",
            })
            if result.status == 200 and validation.valid and same_host(result.final_url, root):
                verified = result.final_url
                break

    status = choose_status(feed_records, verified)
    evidence = {
        "native_only": True,
        "verified": bool(verified),
        "tested_candidate_count": len(feed_records),
        "discovery_endpoint_count": len(discovery),
        "discovered_url_count": len(discovered_urls),
        "records": feed_records,
        "discovery_statuses": [
            {"url": r.requested_url, "final_url": r.final_url, "status": r.status, "content_type": r.content_type, "elapsed_ms": r.elapsed_ms, "error": r.error}
            for r in discovery
        ],
    }
    return SiteResult(site, root, status, verified, evidence, round(time.monotonic() - started, 3))


def run_shard(shard: int, shards: int, output_dir: Path) -> list[SiteResult]:
    selected = [item for index, item in enumerate(TARGETS) if index % shards == shard for item in [item]]
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[SiteResult] = []
    for site, root in selected:
        result = probe_site(site, root)
        results.append(result)
        slug = re.sub(r"[^a-z0-9]+", "-", site.lower()).strip("-")
        (output_dir / f"{slug}.json").write_text(json.dumps(asdict(result), indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / "verified-native-feed-urls.tsv").write_text(
        "\n".join(f"{r.site}\t{r.native_feed_url}" for r in results if r.native_feed_url) + ("\n" if any(r.native_feed_url for r in results) else ""),
        encoding="utf-8",
    )
    return results


def aggregate(artifact_root: Path, output_file: Path) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    for path in sorted(artifact_root.glob("shard-*/**/*.json")):
        if path.name == "manifest.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and "site" in data and "root" in data:
            rows.append(data)
    rows.sort(key=lambda r: str(r["site"]).lower())
    verified = [
        {"site": r["site"], "url": r["native_feed_url"]}
        for r in rows if r.get("native_feed_url")
    ]
    manifest = {
        "schema": "woocommerce-native-google-feed-manifest/v1",
        "native_only": True,
        "sites_total": len(TARGETS),
        "sites_present": len(rows),
        "verified_native_feed_count": len(verified),
        "verified_native_feeds": verified,
        "no_reconstruction": True,
        "results": rows,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    return manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, choices=range(8))
    parser.add_argument("--shards", type=int, default=8)
    parser.add_argument("--output-dir", default="out/native-google-feed-hunt")
    parser.add_argument("--aggregate-dir")
    parser.add_argument("--output-file", default="out/native-google-feed-manifest.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.aggregate_dir:
        manifest = aggregate(Path(args.aggregate_dir), Path(args.output_file))
        print(json.dumps({
            "sites_total": manifest["sites_total"],
            "sites_present": manifest["sites_present"],
            "verified_native_feed_count": manifest["verified_native_feed_count"],
            "verified_native_feeds": manifest["verified_native_feeds"],
        }, indent=2))
        return 0
    if args.shard is None:
        raise SystemExit("--shard is required unless --aggregate-dir is used")
    if not 0 <= args.shard < args.shards:
        raise SystemExit("invalid shard")
    results = run_shard(args.shard, args.shards, Path(args.output_dir))
    print(json.dumps({
        "shard": args.shard,
        "sites": len(results),
        "verified_native_feed_count": sum(bool(r.native_feed_url) for r in results),
        "verified_native_feeds": [
            {"site": r.site, "url": r.native_feed_url} for r in results if r.native_feed_url
        ],
        "statuses": {r.site: r.status for r in results},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
