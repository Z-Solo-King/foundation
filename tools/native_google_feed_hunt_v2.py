#!/usr/bin/env python3
"""Fast, native-only WooCommerce Google Merchant XML URL hunt."""
from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
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

UA = "Mozilla/5.0 (compatible; WooCommerceNativeGoogleFeedHunt/2026.09)"
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

DISCOVERY_PATHS = ("/", "/robots.txt", "/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml", "/wp-json/")

CTXFEED_PATHS = tuple(f"/wp-json/ctxfeed/{v}/feeds" for v in ("v8","v7","v6","v5","v4","v3","v2","v1"))

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


def fetch(url: str, timeout: float, cookie_header: str = "") -> Fetch:
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


def batch(urls: list[str], timeout: float, workers: int, records: list[dict[str, object]]) -> str | None:
    if not urls:
        return None
    valid: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        future_map = {pool.submit(fetch, u, timeout): u for u in urls}
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
            if result.status == 200 and validation.valid and same_host(result.final_url, result.requested_url):
                valid.append(result.final_url)
    return min(valid, key=feed_priority) if valid else None


def probe_site(site: str, root: str) -> SiteResult:
    started = time.monotonic()
    records: list[dict[str, object]] = []
    discovered: set[str] = set()

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(fetch, urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 15.0) for p in DISCOVERY_PATHS]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result.status == 200 and result.body:
                text = result.body.decode("utf-8", "replace")
                discovered.update(extract_urls(text, root))

    ctx_candidates: set[str] = set()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        ctx_results = pool.map(lambda p: fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 12.0), CTXFEED_PATHS)
        for result in ctx_results:
            if result.status == 200 and result.body:
                ctx_candidates.update(ctxfeed_urls(result.body.decode("utf-8", "replace"), root))

    fast_candidates = [urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in FAST_PATHS]
    fast_candidates.extend(sorted(ctx_candidates))
    verified = batch(list(dict.fromkeys(fast_candidates)), 20.0, 8, records)
    if verified is None:
        verified = batch([urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in SLOW_GPF_PATHS], 105.0, 4, records)
    if verified is None:
        verified = batch([urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")) for p in MEDIUM_PATHS], 45.0, 8, records)

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        directory_results = pool.map(lambda p: (p, fetch(urllib.parse.urljoin(root.rstrip("/") + "/", p.lstrip("/")), 12.0)), DIRECTORIES)
        for directory, result in directory_results:
            if result.status == 200 and result.body:
                discovered.update(directory_urls(result.body.decode("utf-8", "replace"), root))

    if verified is None and discovered:
        candidates = sorted(
            (u for u in discovered if urllib.parse.urlsplit(u).path.lower().endswith((".xml", ".xml.gz")) or re.search(r"(feed|merchant|shopping|woocommerce_gpf)", u, re.I)),
        )[:120]
        verified = batch(candidates, 60.0, 8, records)

    status_codes = [int(r.get("status") or 0) for r in records]
    status = "verified_native" if verified else ("transport_blocked" if any(x in {401,403,429} for x in status_codes) else "candidate_negative_or_unverified")
    evidence = {
        "native_only": True,
        "verified": bool(verified),
        "tested_candidate_count": len(records),
        "discovered_url_count": len(discovered),
        "records": records,
    }
    return SiteResult(site, root, status, verified, evidence, round(time.monotonic() - started, 3))


def run_shard(shard: int, shards: int, output_dir: Path) -> list[SiteResult]:
    selected = [target for idx, target in enumerate(TARGETS) if idx % shards == shard]
    output_dir.mkdir(parents=True, exist_ok=True)
    results: list[SiteResult] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        future_map = {pool.submit(probe_site, site, root): site for site, root in selected}
        for future in concurrent.futures.as_completed(future_map):
            result = future.result()
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
    for path in sorted(root.glob("native-google-feed-shard-*/*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict) and "site" in data and "root" in data:
            rows.append(data)
    rows.sort(key=lambda x: str(x["site"]).lower())
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
    args = parser.parse_args()

    if args.aggregate_dir:
        manifest = aggregate(Path(args.aggregate_dir), Path(args.output_file))
        print(json.dumps({k: manifest[k] for k in ("sites_total","sites_present","verified_native_feed_count","verified_native_feeds")}, indent=2))
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
        "verified_native_feeds": [{"site": r.site, "url": r.native_feed_url} for r in results if r.native_feed_url],
        "statuses": {r.site: r.status for r in results},
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
