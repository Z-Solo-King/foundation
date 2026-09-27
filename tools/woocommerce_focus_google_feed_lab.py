#!/usr/bin/env python3
"""
Focused WooCommerce Google Merchant XML discovery lab.

Scope is intentionally limited to Avika Retails and KRGKart.
The lab tries 100 named discovery strategies per retailer and may issue
multiple public probes per strategy. It never requests admin credentials,
never reconstructs a feed, and never treats a sitemap or Store API response
as a Google Merchant feed.

Only a live URL whose response validates as native Google Merchant XML is
written to the verified feed output.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import gzip
import hashlib
import html
import ipaddress
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

UA = "Mozilla/5.0 (compatible; WooCommerceFocusedGoogleFeedLab/2026.09)"
GOOGLE_NS = "http://base.google.com/ns/1.0"
BLOCK_MARKERS = (
    "just a moment",
    "cf-chl-",
    "cf-turnstile",
    "captcha",
    "access denied",
    "attention required",
    "checking your browser",
)
ITEM_TAGS = {"item", "entry"}
SITEMAP_ROOTS = {"urlset", "sitemapindex"}

TARGETS = (
    ("avikaretails", "https://www.avikaretails.com"),
    ("krgkart", "https://krgkart.com"),
)

@dataclass(frozen=True)
class Validation:
    valid: bool
    format: str
    product_items: int
    google_fields: int
    reasons: tuple[str, ...] = ()
    sha256: str = ""

@dataclass
class ProbeResult:
    test_id: str
    strategy: str
    layer: str
    requested_url: str | None = None
    method: str = "GET"
    status: int = 0
    content_type: str = ""
    final_url: str = ""
    elapsed_ms: int = 0
    validation: dict[str, Any] = field(default_factory=dict)
    candidate_urls: list[str] = field(default_factory=list)
    note: str = ""
    error: str | None = None

@dataclass
class SiteState:
    site: str
    root: str
    started: float
    cookies: str = ""
    homepage_html: str = ""
    homepage_headers: dict[str, str] = field(default_factory=dict)
    product_urls: list[str] = field(default_factory=list)
    discovered_routes: set[str] = field(default_factory=set)
    explicit_external_feed_urls: set[str] = field(default_factory=set)
    browser_requests: set[str] = field(default_factory=set)
    browser_response_feed_urls: set[str] = field(default_factory=set)
    search_candidate_urls: set[str] = field(default_factory=set)
    archive_candidate_urls: set[str] = field(default_factory=set)
    ai_candidate_urls: set[str] = field(default_factory=set)
    probes: list[ProbeResult] = field(default_factory=list)
    verified_urls: set[str] = field(default_factory=set)

def host_key(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower().removeprefix("www.").rstrip(".")

def same_host(a: str, b: str) -> bool:
    return bool(host_key(a) and host_key(a) == host_key(b))

def safe_url(raw: str, root: str, allow_external: bool = False) -> str | None:
    raw = html.unescape(str(raw or "")).strip().rstrip(".,);")
    if not raw:
        return None
    try:
        u = urllib.parse.urljoin(root.rstrip("/") + "/", raw)
        p = urllib.parse.urlsplit(u)
        host = (p.hostname or "").lower().rstrip(".")
        if p.scheme not in {"http", "https"} or not host or p.username or p.password:
            return None
        if host.endswith((".local", ".internal", ".lan")) or host in {"localhost", "localhost.localdomain"}:
            return None
        try:
            ip = ipaddress.ip_address(host)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
                return None
        except ValueError:
            pass
        if not allow_external and not same_host(u, root):
            return None
        return u
    except ValueError:
        return None

def looks_feed_url(url: str) -> bool:
    return bool(re.search(
        r"\.xml(?:\.gz)?(?:[?#].*)?$|feed|merchant|shopping|woocommerce_gpf|google|woo[-_]?feed|wppfm|product[-_]?feed",
        url,
        re.I,
    ))

def explicit_feed_urls(text: str, root: str) -> set[str]:
    decoded = html.unescape(text or "")
    found: set[str] = set()

    # Feed configuration keys can legitimately reference a feed host that is
    # different from the storefront host.
    patterns = (
        r"(?:feed[_-]?(?:url|file|path)|xml[_-]?url|export[_-]?url|"
        r"product[_-]?feed|google[_-]?feed|merchant[_-]?feed|shopping[_-]?feed)"
        r"\s*[:=]\s*[\"']([^\"']+)[\"']",
        r"(?:feed[_-]?(?:url|file|path)|xml[_-]?url|export[_-]?url|"
        r"product[_-]?feed|google[_-]?feed|merchant[_-]?feed|shopping[_-]?feed)"
        r"\s*[:=]\s*([^,}\s]+)",
    )
    for pattern in patterns:
        for m in re.finditer(pattern, decoded, re.I):
            u = safe_url(m.group(1), root, allow_external=True)
            if u and looks_feed_url(u):
                found.add(u)

    for tag in re.findall(r"<link\b[^>]*>", decoded, re.I):
        low = tag.lower()
        if "alternate" not in low or not re.search(r"(rss|atom|xml)", low):
            continue
        m = re.search(r'href\s*=\s*[\"\']([^\"\']+)[\"\']', tag, re.I)
        if m:
            u = safe_url(m.group(1), root, allow_external=True)
            if u:
                found.add(u)
    return found

def validate_native_xml(body: bytes, content_type: str = "") -> Validation:
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
    if any(m in lower for m in BLOCK_MARKERS):
        return Validation(False, "blocked", 0, 0, ("challenge_or_access_denied",))
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return Validation(False, "invalid_xml", 0, 0, ("xml_parse_error",))
    root_name = str(root.tag).rsplit("}", 1)[-1].lower()
    if root_name in SITEMAP_ROOTS:
        return Validation(False, "sitemap", 0, 0, ("sitemap_excluded",))
    items = [n for n in root.iter() if str(n.tag).rsplit("}", 1)[-1].lower() in ITEM_TAGS]
    ns_fields = {
        str(n.tag).rsplit("}", 1)[-1].lower()
        for n in root.iter()
        if isinstance(n.tag, str) and n.tag.startswith("{" + GOOGLE_NS + "}")
    }
    valid_items = 0
    for item in items:
        google_fields = {
            str(n.tag).rsplit("}", 1)[-1].lower()
            for n in item.iter()
            if isinstance(n.tag, str) and n.tag.startswith("{" + GOOGLE_NS + "}")
        }
        rss_fields = {
            str(n.tag).rsplit("}", 1)[-1].lower()
            for n in item
            if isinstance(n.tag, str) and not n.tag.startswith("{")
        }
        title_ok = "title" in google_fields or "title" in rss_fields
        link_ok = "link" in google_fields or "link" in rss_fields
        if {"id", "price"}.issubset(google_fields) and title_ok and link_ok:
            valid_items += 1
    reasons = (
        f"root={root_name}",
        f"items={len(items)}",
        f"valid_items={valid_items}",
        f"google_fields={len(ns_fields)}",
        f"content_type={content_type}",
    )
    return Validation(
        bool(valid_items),
        "rss_or_atom" if root_name in {"rss", "feed", "channel"} else "xml",
        len(items),
        len(ns_fields),
        reasons,
        hashlib.sha256(raw).hexdigest() if valid_items else "",
    )

def cookie_header_from_netscape(path: str) -> str:
    pairs = []
    try:
        for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line or line.startswith("#") or "\t" not in line:
                continue
            cols = line.split("\t")
            if len(cols) >= 7 and cols[6]:
                pairs.append(f"{cols[5]}={cols[6]}")
    except OSError:
        return ""
    return "; ".join(dict.fromkeys(pairs))

def curl_fetch(url: str, timeout: float = 15.0, cookies: str = "", method: str = "GET", referer: str = "") -> tuple[int, str, str, bytes, int, str | None]:
    started = time.monotonic()
    meta_path = body_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="focus-meta-", delete=False) as meta, tempfile.NamedTemporaryFile(prefix="focus-body-", delete=False) as body:
            meta_path, body_path = meta.name, body.name
        cmd = [
            "curl", "--silent", "--show-error", "--location", "--compressed",
            "--connect-timeout", "10", "--max-time", str(int(timeout)),
            "-A", UA,
            "-H", "Accept: application/xml, application/rss+xml, text/xml, application/json, text/html;q=0.9, */*;q=0.1",
            "-H", "Accept-Language: en-IN,en;q=0.9",
        ]
        if cookies:
            cmd += ["-H", f"Cookie: {cookies}"]
        if referer:
            cmd += ["-H", f"Referer: {referer}"]
        if method == "HEAD":
            cmd += ["-I"]
        else:
            cmd += ["-o", body_path]
        cmd += ["-w", "%{http_code}\n%{content_type}\n%{url_effective}\n", url]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 8, check=False)
        meta = proc.stdout.splitlines()
        status = int(meta[0]) if meta and meta[0].isdigit() else 0
        content_type = meta[1] if len(meta) > 1 else ""
        final_url = meta[2] if len(meta) > 2 else url
        body = Path(body_path).read_bytes() if body_path and Path(body_path).exists() and method != "HEAD" else b""
        err = None if proc.returncode == 0 else ("curl_timeout" if proc.returncode == 28 else f"curl_exit_{proc.returncode}")
        return status, content_type, final_url, body, int((time.monotonic() - started) * 1000), err
    except subprocess.TimeoutExpired:
        return 0, "", url, b"", int((time.monotonic() - started) * 1000), "curl_process_timeout"
    except Exception as exc:
        return 0, "", url, b"", int((time.monotonic() - started) * 1000), type(exc).__name__
    finally:
        for p in (meta_path, body_path):
            if p:
                try:
                    Path(p).unlink(missing_ok=True)
                except OSError:
                    pass

def safe_record(state: SiteState, test_id: str, strategy: str, layer: str, url: str | None, result: ProbeResult) -> None:
    state.probes.append(result)
    if result.validation.get("valid"):
        if result.final_url:
            state.verified_urls.add(result.final_url)
    if result.candidate_urls:
        state.discovered_routes.update(result.candidate_urls)

def probe_url(state: SiteState, test_id: str, strategy: str, layer: str, url: str, timeout: float = 15.0, method: str = "GET", allow_external: bool = False) -> ProbeResult:
    candidate = safe_url(url, state.root, allow_external=allow_external)
    if not candidate:
        return ProbeResult(test_id, strategy, layer, url, method, error="unsafe_or_invalid_url")
    status, ct, final_url, body, elapsed, err = curl_fetch(candidate, timeout, state.cookies, method, state.root)
    validation = validate_native_xml(body, ct) if method != "HEAD" and status == 200 else Validation(False, "not_checked", 0, 0, ())
    result = ProbeResult(
        test_id, strategy, layer, candidate, method, status, ct, final_url, elapsed,
        asdict(validation), [], "", err,
    )
    if body and method != "HEAD":
        if "json" in ct.lower() or candidate.rstrip("/").endswith(("/wp-json", "/wp-json/")):
            state.discovered_routes.update(parse_wp_json_routes(body, state.root))
        txt = body.decode("utf-8", "replace")
        for u in explicit_feed_urls(txt, state.root):
            state.explicit_external_feed_urls.add(u)
        for raw in re.findall(r'https?://[^\s<>"\'\]\[)]+', txt):
            u = safe_url(raw, state.root, allow_external=allow_external)
            if u and looks_feed_url(u):
                result.candidate_urls.append(u)
        for raw in re.findall(r'(?:href|src|url|feedUrl|feed_url|xml_url|product_feed|google_feed)\s*[:=]\s*[\"\']([^\"\']+)[\"\']', txt, re.I):
            u = safe_url(raw, state.root, allow_external=allow_external)
            if u and looks_feed_url(u):
                result.candidate_urls.append(u)
    safe_record(state, test_id, strategy, layer, candidate, result)
    return result

def warm_session(state: SiteState) -> None:
    jar = tempfile.NamedTemporaryFile(prefix="focus-cookie-", delete=False).name
    try:
        cmd = [
            "curl", "--silent", "--show-error", "--location", "--compressed",
            "--connect-timeout", "10", "--max-time", "20",
            "-A", UA, "-H", "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.1",
            "-H", "Accept-Language: en-IN,en;q=0.9",
            "-c", jar, "-o", "/dev/null", state.root.rstrip("/") + "/",
            "-w", "%{http_code}",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=28, check=False)
        if proc.returncode == 0 and (proc.stdout or "").strip() == "200":
            state.cookies = cookie_header_from_netscape(jar)
    except Exception:
        pass
    finally:
        Path(jar).unlink(missing_ok=True)

def extract_candidate_urls(text: str, root: str, allow_external: bool = True) -> set[str]:
    decoded = html.unescape(text or "")
    found: set[str] = set()
    patterns = [
        r'https?://[^\s<>"\'\]\[)]+',
        r'(?:href|src|url|feedUrl|feed_url|xml_url|product_feed|google_feed)\s*[:=]\s*[\"\']([^\"\']+)[\"\']',
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, decoded, re.I):
            raw = m.group(1) if m.lastindex else m.group(0)
            u = safe_url(raw, root, allow_external=allow_external)
            if u:
                found.add(u)
    return {u for u in found if looks_feed_url(u)}

def parse_wp_json_routes(payload: bytes, root: str) -> set[str]:
    try:
        obj = json.loads(payload.decode("utf-8", "replace"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return set()
    found: set[str] = set()
    text = json.dumps(obj, ensure_ascii=False)
    for key, value in re.findall(r'"([^"]+)"\s*:\s*"([^"]+)"', text):
        if any(k in key.lower() for k in ("feed", "product", "merchant", "google", "xml", "export", "woo")):
            if value.startswith("/"):
                u = safe_url(value, root)
                if u:
                    found.add(u)
        elif looks_feed_url(value):
            u = safe_url(value, root, allow_external=True)
            if u:
                found.add(u)
    # WP API root commonly stores route templates in a "routes" object.
    for raw in re.findall(r'"(/[^"]*(?:feed|product|merchant|google|woo|export|xml)[^"]*)"', text, re.I):
        u = safe_url(raw, root)
        if u:
            found.add(u)
    return found

def google_search(query: str, engine_url: str) -> set[str]:
    q = urllib.parse.quote_plus(query)
    url = engine_url.format(q=q)
    try:
        status, ct, final, body, _, _ = curl_fetch(url, 15)
        if status != 200 or not body:
            return set()
        txt = html.unescape(body.decode("utf-8", "replace"))
        out = set()
        for raw in re.findall(r'https?://[^\s<>"\']+', txt):
            raw = raw.replace("&amp;", "&")
            if ".xml" in raw.lower() or "feed" in raw.lower() or "merchant" in raw.lower():
                out.add(raw.rstrip(").,"))
        return out
    except Exception:
        return set()

def public_archive_urls(root: str) -> set[str]:
    host = host_key(root)
    found: set[str] = set()

    def run_json(cmd: list[str], timeout: int = 30) -> list[dict[str, Any]]:
        try:
            p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        except Exception:
            return []
        out = (p.stdout or "").strip()
        if not out:
            return []
        try:
            parsed = json.loads(out)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], list):
            header = [str(x) for x in parsed[0]]
            return [
                {header[i]: row[i] if i < len(row) else "" for i in range(len(header))}
                for row in parsed[1:] if isinstance(row, list)
            ]
        if isinstance(parsed, list) and all(isinstance(x, dict) for x in parsed):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
        return []

    try:
        p = subprocess.run(
            ["curl","--silent","--show-error","--location","--connect-timeout","8","--max-time","20","-A",UA,"https://index.commoncrawl.org/collinfo.json"],
            capture_output=True, text=True, timeout=28, check=False,
        )
        info = json.loads(p.stdout or "[]")
        indexes = [str(x.get("id","")) for x in info if isinstance(x, dict) and str(x.get("id","")).startswith("CC-MAIN-")][:2]
    except Exception:
        indexes = []

    for idx in indexes:
        params = urllib.parse.urlencode({"url": f"{host}/*", "output": "json", "filter": "status:200", "pageSize": "300"})
        rows = run_json(["curl","--silent","--show-error","--location","--connect-timeout","8","--max-time","25","-A",UA,f"https://index.commoncrawl.org/{idx}-index?{params}"], 32)
        for row in rows:
            for key in ("url", "original"):
                raw = str(row.get(key) or "")
                u = safe_url(raw, root)
                if u and looks_feed_url(u):
                    found.add(u)
    params = urllib.parse.urlencode({
        "url": f"{host}/*", "output": "json",
        "fl": "timestamp,original,mimetype,statuscode",
        "filter": "statuscode:200", "collapse": "urlkey", "limit": "500",
    })
    rows = run_json(["curl","--silent","--show-error","--location","--connect-timeout","8","--max-time","25","-A",UA,f"https://web.archive.org/cdx/search/cdx?{params}"], 32)
    for row in rows:
        raw = str(row.get("original") or "")
        u = safe_url(raw, root)
        if u and looks_feed_url(u):
            found.add(u)
    return found

def ai_candidates(label: str, root: str, evidence: dict[str, Any], provider: str, api_key: str, model: str) -> set[str]:
    if not api_key:
        return set()
    prompt = (
        "You are a web integration diagnostician. We are looking for an existing public "
        "Google Merchant product feed URL for a WooCommerce retailer. Do not invent a "
        "feed, do not reconstruct XML, and do not use credentials. Based only on the public "
        "evidence below, return JSON: {\"urls\":[...],\"routes\":[...]} with concrete "
        "candidate URLs or route patterns that should be live-validated. Prefer plugin-specific "
        "feed endpoints, query parameters, generated filename conventions, REST routes, or "
        "explicitly exposed feed hosts. Empty arrays are allowed.\n\n"
        f"Retailer={label}\nRoot={root}\nEvidence={json.dumps(evidence)[:30000]}"
    )
    try:
        if provider == "groq":
            data = json.dumps({
                "model": model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": "Return only compact JSON."},
                    {"role": "user", "content": prompt},
                ],
            }).encode()
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=data,
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=35) as r:
                raw = r.read()
            obj = json.loads(raw.decode("utf-8", "replace"))
            text_out = obj["choices"][0]["message"]["content"]
        else:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{urllib.parse.quote(model)}:generateContent"
            payload = json.dumps({
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0, "response_mime_type": "application/json"},
            }).encode()
            req = urllib.request.Request(
                endpoint,
                data=payload,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=35) as r:
                raw = r.read()
            obj = json.loads(raw.decode("utf-8", "replace"))
            text_out = obj["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(text_out)
        raw_items = list(parsed.get("urls", [])) + list(parsed.get("routes", []))
    except Exception:
        return set()
    found = set()
    for raw in raw_items:
        u = safe_url(str(raw), root, allow_external=True)
        if u and looks_feed_url(u):
            found.add(u)
    return found

def strategy_specs() -> list[tuple[str, str, str, list[str]]]:
    specs: list[tuple[str,str,str,list[str]]] = []

    def add(layer: str, category: str, urls: list[str]) -> None:
        specs.append((layer, category, category, urls))

    # 01-10 canonical WooCommerce GPF variants.
    canonical = [
        "/?woocommerce_gpf=google",
        "/woocommerce_gpf/google",
        "/index.php?woocommerce_gpf=google",
        "/?woocommerce_gpf=google&format=xml",
        "/?woocommerce_gpf=google&output=xml",
        "/?woocommerce_gpf=google&type=xml",
        "/?woocommerce_gpf=google&feed=xml",
        "/?woocommerce_gpf=google&gpf=1",
        "/?woocommerce_gpf=google&lang=en",
        "/?woocommerce_gpf=google&currency=INR",
    ]
    for i, u in enumerate(canonical, 1):
        specs.append(("T%03d" % i, f"GPF canonical variant {i}", "gpf", [u]))

    # 11-20 slicing / parameter permutations.
    slices = [
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=25",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=50",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
        "/?woocommerce_gpf=google&gpf_start=1&gpf_limit=100",
        "/?woocommerce_gpf=google&gpf_start=100&gpf_limit=100",
        "/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
        "/woocommerce_gpf/google?gpf_start=0&gpf_limit=500",
    ]
    for i, u in enumerate(slices, 11):
        specs.append(("T%03d" % i, f"GPF pagination variant {i-10}", "gpf", [u]))

    # 21-30 plugin/static upload naming.
    plugin = [
        "/wp-content/uploads/woo-feed/google/xml/google.xml",
        "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
        "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
        "/wp-content/uploads/woo-feed/google.xml",
        "/wp-content/uploads/woo-feed/google-feed.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
        "/wp-content/uploads/wppfm-feeds/google.xml",
        "/wp-content/uploads/codesolz-feeds/google-products.xml",
    ]
    for i, u in enumerate(plugin, 21):
        specs.append(("T%03d" % i, f"Plugin upload filename {i-20}", "plugin", [u]))

    # 31-40 generic feed names and extensions.
    generic = [
        "/google.xml",
        "/google_feed.xml",
        "/google-feed.xml",
        "/google-products.xml",
        "/google-product-feed.xml",
        "/google-shopping.xml",
        "/google-shopping-feed.xml",
        "/google-merchant.xml",
        "/google-merchant-feed.xml",
        "/merchant-feed.xml",
    ]
    for i, u in enumerate(generic, 31):
        specs.append(("T%03d" % i, f"Generic Google XML path {i-30}", "generic", [u]))

    # 41-50 more generic path grammar.
    generic2 = [
        "/product-feed.xml",
        "/product_feed.xml",
        "/productfeed.xml",
        "/feed/google.xml",
        "/feeds/google.xml",
        "/feed/google-feed.xml",
        "/feed/google-products.xml",
        "/feeds/google-products.xml",
        "/feeds/google-product-feed.xml",
        "/google-shopping-products.xml",
    ]
    for i, u in enumerate(generic2, 41):
        specs.append(("T%03d" % i, f"Generic feed grammar {i-40}", "generic", [u]))

    # 51-60 WordPress REST roots / versions.
    rest = [
        "/wp-json/",
        "/wp-json/wp/v1/",
        "/wp-json/wp/v2/",
        "/wp-json/wp/v3/",
        "/wp-json/wp/v2/types",
        "/wp-json/wp/v2/product",
        "/wp-json/wp/v2/product_cat",
        "/index.php?rest_route=/",
        "/?rest_route=/wp/v2/",
        "/?rest_route=/wp/v3/",
    ]
    for i, u in enumerate(rest, 51):
        specs.append(("T%03d" % i, f"WordPress REST probe {i-50}", "wp-rest", [u]))

    # 61-70 WooCommerce / Store API versions.
    wc = [
        "/wp-json/wc/v1/",
        "/wp-json/wc/v2/",
        "/wp-json/wc/v3/",
        "/wp-json/wc/store/v1/",
        "/wp-json/wc/store/v1/products?per_page=1",
        "/wp-json/wc/store/v1/products?per_page=1&orderby=date",
        "/wp-json/wc/store/v1/products?search=ssd&per_page=1",
        "/?rest_route=/wc/store/v1/products&per_page=1",
        "/?rest_route=/wc/v1/products&per_page=1",
        "/?rest_route=/wc/v2/products&per_page=1",
    ]
    for i, u in enumerate(wc, 61):
        specs.append(("T%03d" % i, f"WooCommerce REST probe {i-60}", "wc-rest", [u]))

    # 71-80 plugin namespaces / public feed routes.
    ns = [
        "/wp-json/feedcraft-product-feed/v1/xml",
        "/wp-json/feedcraft-product-feed/v1/google.xml",
        "/wp-json/feed-products/v1/google.xml",
        "/wp-json/google-product-feed/v1/xml",
        "/wp-json/google-feed/v1/xml",
        "/wp-json/woo-feed/v1/google.xml",
        "/wp-json/ctxfeed/v8/feeds",
        "/wp-json/ctxfeed/v7/feeds",
        "/wp-json/ctxfeed/v6/feeds",
        "/wp-json/ctxfeed/v5/feeds",
    ]
    for i, u in enumerate(ns, 71):
        specs.append(("T%03d" % i, f"Plugin REST namespace {i-70}", "plugin-rest", [u]))

    # 81-90 robots/sitemaps/directories/alternate access.
    discovery = [
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/sitemap.rss",
        "/wp-sitemap.xml",
        "/product-sitemap.xml",
        "/wp-json/oembed/1.0/embed?url=/",
        "/?feed=rss2",
        "/feed/",
        "/comments/feed/",
    ]
    for i, u in enumerate(discovery, 81):
        specs.append(("T%03d" % i, f"Public discovery surface {i-80}", "discovery", [u]))

    # 91-100 static/generated filename patterns and alternate query syntax.
    final_paths = [
        "/wp-content/uploads/woo-feed/google/",
        "/wp-content/uploads/woo-feed/google/xml/",
        "/wp-content/uploads/woo-product-feed-pro/xml/",
        "/wp-content/uploads/wppfm-feeds/",
        "/wp-content/uploads/codesolz-feeds/",
        "/feeds/",
        "/feed/",
        "/?feed=google",
        "/?feed=merchant",
        "/?feed=google-shopping",
    ]
    for i, u in enumerate(final_paths, 91):
        specs.append(("T%03d" % i, f"Directory/query recovery probe {i-90}", "recovery", [u]))

    assert len(specs) == 100, len(specs)
    return specs

def browser_discovery(state: SiteState, max_products: int = 3) -> None:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        state.probes.append(ProbeResult("T101","Playwright availability","browser",error=type(exc).__name__))
        return

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            locale="en-IN",
            user_agent=UA,
            viewport={"width": 1440, "height": 900},
        )
        page = context.new_page()

        def on_request(req) -> None:
            url = str(req.url)
            state.browser_requests.add(url)
            if safe_url(url, state.root, allow_external=True) and looks_feed_url(url):
                if same_host(url, state.root):
                    state.discovered_routes.add(url)
                else:
                    state.explicit_external_feed_urls.add(url)

        def on_response(resp) -> None:
            url = str(resp.url)
            if not safe_url(url, state.root, allow_external=True):
                return
            try:
                ct = str(resp.headers.get("content-type", "")).lower()
                interesting = "xml" in ct or "rss" in ct or "atom" in ct or looks_feed_url(url)
                if not interesting:
                    return
                body = resp.body()
                val = validate_native_xml(body, ct)
                if val.valid:
                    state.browser_response_feed_urls.add(url)
                    state.verified_urls.add(url)
                    if not same_host(url, state.root):
                        state.explicit_external_feed_urls.add(url)
                elif same_host(url, state.root) and len(body) <= 2_000_000:
                    state.discovered_routes.update(extract_candidate_urls(body.decode("utf-8", "replace"), state.root, allow_external=False))
            except Exception:
                pass

        page.on("request", on_request)
        page.on("response", on_response)

        start = time.monotonic()
        try:
            page.goto(state.root.rstrip("/") + "/", wait_until="domcontentloaded", timeout=40000)
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            state.homepage_html = page.content()
            state.explicit_external_feed_urls.update(explicit_feed_urls(state.homepage_html, state.root))
            state.discovered_routes.update(extract_candidate_urls(state.homepage_html, state.root, allow_external=False))
            script_srcs = page.locator("script[src]").evaluate_all("(els)=>els.map(e=>e.src).filter(Boolean)")
            script_srcs = list(dict.fromkeys(str(x) for x in script_srcs))[:40]
            for script_url in script_srcs:
                try:
                    response = context.request.get(script_url, timeout=15000)
                    if response.ok:
                        script_body = response.body().decode("utf-8", "replace")
                        state.discovered_routes.update(extract_candidate_urls(script_body, state.root, allow_external=False))
                        state.explicit_external_feed_urls.update(explicit_feed_urls(script_body, state.root))
                except Exception:
                    pass
            state.probes.append(ProbeResult(
                "T106","Homepage JavaScript asset mining","browser",
                state.root,"GET",200,"text/html",page.url,0,{"valid":False},
                sorted(state.discovered_routes)[:150],f"scripts_checked={len(script_srcs)}",
            ))

            hrefs = page.locator("a[href]").evaluate_all("(els)=>els.map(e=>e.href).filter(Boolean)")
            for href in hrefs:
                u = safe_url(str(href), state.root, allow_external=False)
                if u and ("/product/" in u or "/products/" in u):
                    state.product_urls.append(u)
            state.product_urls = list(dict.fromkeys(state.product_urls))[:max_products]

            perf = page.evaluate("performance.getEntriesByType('resource').map(e=>e.name)")
            for raw in perf:
                u = safe_url(str(raw), state.root, allow_external=False)
                if u:
                    state.browser_requests.add(u)
                    if looks_feed_url(u):
                        state.discovered_routes.add(u)

            page.evaluate("document.documentElement.outerHTML")
            sw = page.evaluate(
                "navigator.serviceWorker ? navigator.serviceWorker.getRegistrations().then(rs=>rs.map(r=>r.scope)) : Promise.resolve([])"
            )
            if isinstance(sw, list):
                for raw in sw:
                    u = safe_url(str(raw), state.root, allow_external=False)
                    if u:
                        state.discovered_routes.add(u)

            state.probes.append(ProbeResult(
                "T102","Playwright homepage render/XHR","browser",
                state.root, "GET", 200, "text/html", page.url,
                int((time.monotonic()-start)*1000), {"valid": bool(state.verified_urls)},
                sorted(state.discovered_routes)[:200],
                f"requests={len(state.browser_requests)} products={len(state.product_urls)}",
            ))

            for idx, product in enumerate(state.product_urls[:max_products], 1):
                before = len(state.browser_requests)
                try:
                    page.goto(product, wait_until="domcontentloaded", timeout=30000)
                    try:
                        page.wait_for_load_state("networkidle", timeout=7000)
                    except Exception:
                        pass
                    body = page.content()
                    state.discovered_routes.update(extract_candidate_urls(body, state.root, allow_external=False))
                    state.explicit_external_feed_urls.update(explicit_feed_urls(body, state.root))
                    state.probes.append(ProbeResult(
                        f"T{102+idx:03d}",f"Playwright product page {idx}","browser",
                        product,"GET",200,"text/html",page.url,
                        0,{"valid":False},sorted(state.discovered_routes)[:100],
                        f"new_requests={max(0,len(state.browser_requests)-before)}",
                    ))
                except Exception as exc:
                    state.probes.append(ProbeResult(
                        f"T{102+idx:03d}",f"Playwright product page {idx}","browser",
                        product,error=type(exc).__name__,
                    ))
        except Exception as exc:
            state.probes.append(ProbeResult(
                "T102","Playwright homepage render/XHR","browser",
                state.root,error=type(exc).__name__,
            ))
        finally:
            browser.close()

def run_gsc_optional(state: SiteState) -> None:
    token = os.getenv("GSC_ACCESS_TOKEN", "").strip()
    property_url = os.getenv("GSC_PROPERTY", "").strip()
    if not token or not property_url:
        state.probes.append(ProbeResult(
            "T107","Google Search Console submitted-sitemap audit","google",
            note="skipped_no_authorized_gsc_token",
        ))
        return
    endpoint = "https://searchconsole.googleapis.com/webmasters/v3/sites/" + urllib.parse.quote(property_url, safe="") + "/sitemaps"
    try:
        req = urllib.request.Request(endpoint, headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.loads(r.read().decode("utf-8","replace"))
        found = set()
        for item in data.get("sitemap", []):
            u = str(item.get("path") or "")
            if u and looks_feed_url(u):
                found.add(u)
        state.probes.append(ProbeResult(
            "T107","Google Search Console submitted-sitemap audit","google",
            endpoint,"GET",200,"application/json",endpoint,0,{"valid":False},
            sorted(found), f"submitted_xml_like={len(found)}",
        ))
        state.search_candidate_urls.update(found)
    except Exception as exc:
        state.probes.append(ProbeResult("T107","Google Search Console submitted-sitemap audit","google",endpoint,error=type(exc).__name__))

def run_search_archive_ai(state: SiteState) -> None:
    google_queries = [
        f'site:{host_key(state.root)} filetype:xml feed',
        f'site:{host_key(state.root)} inurl:feed google',
        f'site:{host_key(state.root)} "woocommerce_gpf"',
        f'site:{host_key(state.root)} "woo_feed"',
        f'site:{host_key(state.root)} "google-shopping"',
        f'site:{host_key(state.root)} "merchant feed"',
    ]
    engines = [
        "https://www.google.com/search?q={q}",
        "https://www.google.co.in/search?q={q}",
        "https://www.bing.com/search?q={q}",
    ]
    for qi, query in enumerate(google_queries, 1):
        found: set[str] = set()
        for engine in engines:
            found.update(google_search(query, engine))
        found = {u for u in found if host_key(u) == host_key(state.root) or looks_feed_url(u)}
        state.search_candidate_urls.update(found)
        state.probes.append(ProbeResult(
            f"T{107+qi:03d}",f"Public search index query {qi}","search",
            note=query,candidate_urls=sorted(found),
        ))

    archive = public_archive_urls(state.root)
    state.archive_candidate_urls.update(archive)
    state.probes.append(ProbeResult(
        "T114","Common Crawl + Wayback feed URL recovery","archive",
        candidate_urls=sorted(archive), note=f"candidates={len(archive)}",
    ))

    evidence = {
        "homepage_text": re.sub(r"\s+", " ", state.homepage_html)[:7000],
        "browser_requests": sorted(state.browser_requests)[:300],
        "discovered_routes": sorted(state.discovered_routes)[:300],
        "search_candidates": sorted(state.search_candidate_urls)[:200],
        "archive_candidates": sorted(state.archive_candidate_urls)[:200],
    }
    groq = ai_candidates(
        state.site, state.root, evidence, "groq",
        os.getenv("GROQ_API_KEY",""), os.getenv("GROQ_MODEL","qwen/qwen3.6-27b"),
    )
    gemini = ai_candidates(
        state.site, state.root, evidence, "gemini",
        os.getenv("GEMINI_API_KEY",""), os.getenv("GEMINI_MODEL","gemini-3.6-flash"),
    )
    state.ai_candidate_urls.update(groq)
    state.ai_candidate_urls.update(gemini)
    state.probes.append(ProbeResult(
        "T115","Groq candidate generation","ai",candidate_urls=sorted(groq),note=f"count={len(groq)}",
    ))
    state.probes.append(ProbeResult(
        "T116","Gemini candidate generation","ai",candidate_urls=sorted(gemini),note=f"count={len(gemini)}",
    ))

def replay_candidates(state: SiteState) -> None:
    candidates = (
        set(state.explicit_external_feed_urls)
        | set(state.discovered_routes)
        | set(state.search_candidate_urls)
        | set(state.archive_candidate_urls)
        | set(state.ai_candidate_urls)
        | set(state.browser_response_feed_urls)
    )
    candidates = {u for u in candidates if looks_feed_url(u)}
    for idx, url in enumerate(sorted(candidates)[:500], 1):
        # Candidates are hypotheses. Native XML is the only acceptance test.
        result = probe_url(
            state, f"R{idx:03d}", "Candidate live replay",
            "candidate-replay", url, 35.0,
            allow_external=not same_host(url, state.root),
        )
        if result.validation.get("valid"):
            state.verified_urls.add(result.final_url or url)

def run_site(label: str, root: str, output_dir: Path) -> SiteState:
    state = SiteState(label, root, time.monotonic())
    warm_session(state)

    specs = strategy_specs()
    # Core 100 tests run concurrently per site. Each strategy remains a separately
    # identified probe in the evidence manifest; concurrency only removes artificial
    # serial latency.
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        futures = []
        for test_id, name, layer, urls in specs:
            for url in urls:
                futures.append(pool.submit(
                    probe_url,
                    state,
                    test_id,
                    name,
                    layer,
                    urllib.parse.urljoin(root.rstrip("/") + "/", url),
                    10.0,
                ))
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                state.probes.append(ProbeResult(
                    "TERR", "Core strategy exception", "harness", error=type(exc).__name__
                ))

    browser_discovery(state)
    run_gsc_optional(state)
    run_search_archive_ai(state)
    replay_candidates(state)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_out = {
        "site": state.site,
        "root": state.root,
        "native_only": True,
        "no_reconstruction": True,
        "test_count": 100,
        "test_strategy_ids": [x[0] for x in strategy_specs()],
        "verified_feed_urls": sorted(state.verified_urls),
        "counts": {
            "probes": len(state.probes),
            "browser_requests": len(state.browser_requests),
            "discovered_routes": len(state.discovered_routes),
            "external_explicit": len(state.explicit_external_feed_urls),
            "search_candidates": len(state.search_candidate_urls),
            "archive_candidates": len(state.archive_candidate_urls),
            "ai_candidates": len(state.ai_candidate_urls),
        },
        "probes": [asdict(p) for p in state.probes],
    }
    (output_dir / f"{label}.json").write_text(json.dumps(json_out, indent=2, sort_keys=True), encoding="utf-8")
    (output_dir / f"{label}-verified-feed-urls.txt").write_text(
        "\n".join(sorted(state.verified_urls)) + ("\n" if state.verified_urls else ""),
        encoding="utf-8",
    )
    return state

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output-dir", default="out/focused-google-feed-lab")
    args = ap.parse_args()
    out = Path(args.output_dir)

    states: list[SiteState] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futs = [pool.submit(run_site, label, root, out) for label, root in TARGETS]
        for fut in concurrent.futures.as_completed(futs):
            states.append(fut.result())

    manifest = {
        "schema": "focused-woocommerce-google-feed-lab/v1",
        "native_only": True,
        "no_reconstruction": True,
        "targets": [s.root for s in states],
        "verified_feed_urls": [
            {"site": s.site, "url": url}
            for s in sorted(states, key=lambda x: x.site)
            for url in sorted(s.verified_urls)
        ],
        "test_strategy_count_per_site": 100,
        "site_summaries": [
            {
                "site": s.site,
                "root": s.root,
                "verified_feed_urls": sorted(s.verified_urls),
                "probe_count": len(s.probes),
                "browser_request_count": len(s.browser_requests),
                "discovered_route_count": len(s.discovered_routes),
                "search_candidate_count": len(s.search_candidate_urls),
                "archive_candidate_count": len(s.archive_candidate_urls),
                "ai_candidate_count": len(s.ai_candidate_urls),
            }
            for s in sorted(states, key=lambda x: x.site)
        ],
    }
    (out / "focused-google-feed-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out / "verified-native-google-feeds.tsv").write_text(
        "\n".join(f"{row['site']}\t{row['url']}" for row in manifest["verified_feed_urls"]) + (
            "\n" if manifest["verified_feed_urls"] else ""
        ),
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
