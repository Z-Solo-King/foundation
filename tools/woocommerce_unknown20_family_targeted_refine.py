#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

ROOT = Path(__file__).resolve().parents[1]
CAL = Path(os.getenv("REFINEMENT_JSON", ROOT / "aggregate.json"))

TARGET_FAMILIES = {
    "Cosmic Byte": ("https://www.thecosmicbyte.com", "adtribes_product_feed_pro"),
    "NCL Computer": ("https://nclcomputer.com", "webtoffee_product_feed"),
    "PC Kumar Infotech": ("https://pckumar.in", "google_for_woocommerce"),
    "ithunt": ("https://ithunt.in", "google_for_woocommerce"),
}

FAMILY_PATHS = {
    "adtribes_product_feed_pro": [
        "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    ],
    "webtoffee_product_feed": [
        "/wp-content/uploads/webtoffee_product_feed/wt_Google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/google.xml",
        "/wp-content/uploads/webtoffee_product_feed/google-shopping.xml",
    ],
}

FAMILY_DIRS = {
    "adtribes_product_feed_pro": [
        "/wp-content/uploads/woo-product-feed-pro/xml/",
        "/wp-content/uploads/woo-product-feed-pro/",
    ],
    "webtoffee_product_feed": [
        "/wp-content/uploads/webtoffee_product_feed/",
    ],
}

GOOGLE_NS = re.compile(r'xmlns:g\s*=\s*["\']https?://base\.google\.com/ns/1\.0["\']', re.I)
GOOGLE_FIELDS = ("g:id", "g:title", "g:link", "g:price")
CHALLENGE = re.compile(r"just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser", re.I)

def same_host(a: str, b: str) -> bool:
    try:
        return urlsplit(a).hostname.lower().removeprefix("www.") == urlsplit(b).hostname.lower().removeprefix("www.")
    except Exception:
        return False

def feedish(url: str) -> bool:
    p = urlsplit(url).path.lower()
    return p.endswith(".xml") or p.endswith(".xml.gz") or any(x in url.lower() for x in ("feed", "merchant", "shopping", "google", "webtoffee", "adtribes"))

def validate(body: str) -> dict:
    x = str(body or "")
    h = x[:24000]
    if not x.strip():
        return {"valid": False, "reason": "empty"}
    if CHALLENGE.search(h):
        return {"valid": False, "reason": "interstitial_or_access_denied"}
    if re.match(r"\s*<(?:urlset|sitemapindex)\b", x, re.I):
        return {"valid": False, "reason": "sitemap"}
    if not re.search(r"<(?:\?xml\b|rss\b|feed\b|channel\b)", x[:2000], re.I):
        return {"valid": False, "reason": "not_xml"}
    if not GOOGLE_NS.search(x):
        return {"valid": False, "reason": "no_google_namespace"}
    items = re.findall(r"<item\b[^>]*>([\s\S]*?)</item>", x, re.I)
    entries = re.findall(r"<entry\b[^>]*>([\s\S]*?)</entry>", x, re.I)
    good = 0
    for block in items + entries:
        if all(re.search(fr"<{re.escape(f)}\b[^>]*>\s*[^<]+\s*</{re.escape(f)}>", block, re.I) for f in GOOGLE_FIELDS):
            good += 1
    return {"valid": good > 0, "reason": "validated_google_merchant_xml" if good else "no_item_with_core_google_fields", "items": len(items) + len(entries), "valid_items": good}

async def get(client: httpx.AsyncClient, url: str, timeout: float = 10) -> dict:
    try:
        r = await client.get(
            url,
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; WooCommerceFamilyTargetRefine/2026.09)",
                "Accept": "application/xml,text/xml,text/html,application/json;q=0.9,*/*;q=0.1",
                "Accept-Language": "en-IN,en;q=0.9",
            },
        )
        body = r.text[:12 * 1024 * 1024]
        return {"status": r.status_code, "url": r.url.__str__(), "content_type": r.headers.get("content-type", ""), "body": body}
    except Exception as exc:
        return {"status": 0, "url": url, "content_type": "", "body": "", "error": type(exc).__name__}

def extract_xml_links(body: str, base: str) -> list[str]:
    out = set()
    for raw in re.findall(r'(?:href|src|loc|data-href|data-url)\s*=\s*["\']([^"\']+)', body or "", re.I):
        try:
            u = urljoin(base, raw)
            if same_host(u, base) and feedish(u):
                out.add(u)
        except Exception:
            pass
    for raw in re.findall(r"https?://[^\s<>'\"]+", body or "", re.I):
        raw = raw.rstrip("),.;")
        if same_host(raw, base) and feedish(raw):
            out.add(raw)
    return sorted(out)

def google_api_signal(body: str, status: int, url: str) -> bool:
    blob = body or ""
    return status == 200 and (
        re.search(r"wc/gla|google[-_]listings[-_]and[-_]ads|google for woocommerce|google merchant center", blob, re.I)
        or "wc/gla" in url.lower()
    )

async def run_target(name: str, root: str, family: str) -> dict:
    timeout = httpx.Timeout(12.0, connect=8.0)
    async with httpx.AsyncClient() as client:
        home = await get(client, root, timeout=12)
        page_text = home.get("body", "")
        discovered = set(extract_xml_links(page_text, root))

        for p in ("/robots.txt", "/sitemap.xml", "/sitemap_index.xml", "/wp-sitemap.xml", "/wp-json/"):
            r = await get(client, urljoin(root, p), timeout=10)
            discovered.update(extract_xml_links(r.get("body", ""), r.get("url", root)))

        dirs = []
        if family in FAMILY_DIRS:
            for d in FAMILY_DIRS[family]:
                r = await get(client, urljoin(root, d), timeout=8)
                links = [u for u in extract_xml_links(r.get("body", ""), r.get("url", urljoin(root, d))) if urlsplit(u).path.lower().endswith((".xml", ".xml.gz"))]
                dirs.append({"directory": urljoin(root, d), "status": r.get("status"), "links": links[:100]})
                discovered.update(links)

        candidates = set(discovered)
        for p in FAMILY_PATHS.get(family, []):
            candidates.add(urljoin(root, p))

        # Reuse only same-host historical/current XML-looking URLs from the aggregate.
        source_rows = []
        try:
            aggregate = json.loads(CAL.read_text(encoding="utf-8"))
            source_rows = next((x.get("results", []) for x in [aggregate] if x.get("results")), [])
        except Exception:
            source_rows = []
        for row in source_rows:
            if row.get("site") != name:
                continue
            for u in row.get("historical_feed_candidates", []):
                if same_host(u, root) and feedish(u):
                    candidates.add(u)

        checked = []
        sem = asyncio.Semaphore(12)

        async def one(u: str):
            async with sem:
                r = await get(client, u, timeout=15)
                v = validate(r.get("body", ""))
                checked.append({
                    "url": u,
                    "status": r.get("status"),
                    "final_url": r.get("url"),
                    "content_type": r.get("content_type"),
                    "bytes": len(r.get("body", "")),
                    "validation": v,
                })

        if family != "google_for_woocommerce":
            await asyncio.gather(*(one(u) for u in sorted(candidates)[:160]))

        gla_signals = []
        if family == "google_for_woocommerce":
            for p in ("/wp-json/wc/gla/", "/?rest_route=/wc/gla/"):
                r = await get(client, urljoin(root, p), timeout=10)
                gla_signals.append({
                    "url": r.get("url"),
                    "status": r.get("status"),
                    "content_type": r.get("content_type"),
                    "api_signal": google_api_signal(r.get("body", ""), r.get("status", 0), r.get("url", "")),
                })

        native = next((x for x in checked if x["validation"]["valid"]), None)
        result = {
            "site": name,
            "root": root,
            "family_hypothesis": family,
            "family_hypothesis_confidence": "low",
            "directory_results": dirs,
            "candidate_count": len(candidates),
            "checked_count": len(checked),
            "native_feed_verified": bool(native),
            "native_feed": native,
            "google_api_signals": gla_signals,
            "status": (
                "NATIVE_FEED_VERIFIED" if native else
                "API_INTEGRATED_GOOGLE_NO_PUBLIC_XML" if family == "google_for_woocommerce" and any(x["api_signal"] for x in gla_signals) else
                "FAMILY_IDENTIFIED_FEED_FILENAME_UNRESOLVED" if family != "google_for_woocommerce" else
                "FAMILY_HYPOTHESIS_ONLY"
            ),
        }
        print(json.dumps({
            "site": name,
            "family": family,
            "candidate_count": len(candidates),
            "native": bool(native),
            "status": result["status"],
        }), flush=True)
        return result

async def main() -> None:
    aggregate = json.loads(CAL.read_text(encoding="utf-8"))
    selected = []
    for site, (root, family) in TARGET_FAMILIES.items():
        selected.append((site, root, family))

    results = await asyncio.gather(*(run_target(*x) for x in selected))
    out = ROOT / "out" / "woocommerce-family-targeted-refine"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "woocommerce-family-targeted-refine/v1",
        "source_schema": aggregate.get("schema"),
        "targets": [x[0] for x in selected],
        "results": results,
        "native_verified": sum(1 for x in results if x["native_feed_verified"]),
        "api_integrated_google": sum(1 for x in results if x["status"] == "API_INTEGRATED_GOOGLE_NO_PUBLIC_XML"),
    }
    (out / "targeted.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    md = [
        "# WooCommerce Family-Targeted Refinement",
        "",
        f"Targets: {len(results)}",
        f"Native Google Merchant XML verified: {payload['native_verified']}",
        f"Google API-integrated/no public XML: {payload['api_integrated_google']}",
        "",
        "| Site | Hypothesized family | Native feed | Status | Candidates |",
        "|---|---|---|---|---:|",
        *[
            f"| {x['site']} | {x['family_hypothesis']} | {'YES' if x['native_feed_verified'] else 'NO'} | {x['status']} | {x['candidate_count']} |"
            for x in results
        ],
    ]
    (out / "targeted.md").write_text("\n".join(md) + "\n", encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(main())
