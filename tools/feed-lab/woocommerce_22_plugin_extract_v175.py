#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse, urlencode

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

SOURCE_EXTRACTOR_VERSION = "V175"
SCHEMA = "woocommerce-22-plugin-extraction-v175/v1"

SITES = [
    ("AULA India", "https://aulaindia.com"),
    ("Aarna Computers", "https://aarnacomputers.com"),
    ("Ads Store", "https://adsstore.in"),
    ("Cosmic Byte", "https://www.thecosmicbyte.com"),
    ("EZPZ Solutions", "https://www.ezpzsolutions.in"),
    ("KC Computers", "https://kccomputers.co.in"),
    ("KRG KART", "https://krgkart.com"),
    ("Kryptronix Gaming", "https://kryptronix.in"),
    ("Meckeys", "https://www.meckeys.com"),
    ("Moskeys", "https://moskeys.com"),
    ("NCL Computer", "https://nclcomputer.com"),
    ("PC Kumar Infotech", "https://pckumar.in"),
    ("PCHubShop", "https://www.pchubshop.com"),
    ("Prime ABGB", "https://www.primeabgb.com"),
    ("SCL Gaming", "https://sclgaming.in"),
    ("StacksKB", "https://stackskb.com"),
    ("Theproaudio", "https://www.theproaudio.com"),
    ("Variety Infotech", "https://varietyinfotech.com"),
    ("Viper PC", "https://viperpc.in"),
    ("hotshiftpc", "https://hotshiftpc.com"),
    ("itgadgetsonline", "https://itgadgetsonline.com"),
    ("ithunt", "https://ithunt.in"),
]

CHALLENGE_MARKERS = (
    "just a moment", "cf-chl-", "cf-browser-verification", "cf-mitigated",
    "managed_challenge", "attention required", "checking your browser",
    "enable javascript and cookies", "verify you are human", "cf-turnstile",
    "captcha", "challenge-platform", "access denied",
)

KNOWN_FEED_SLUGS = {
    "woocommerce-google-product-feed": "woocommerce_google_product_feed",
    "woo-feed": "ctx_feed_webappick",
    "webappick-product-feed-for-woocommerce": "ctx_feed_webappick",
    "ctx-feed": "ctx_feed_webappick",
    "woo-product-feed-pro": "adtribes_product_feed_pro",
    "merchant-feed-booster-lite-for-woocommerce": "codesolz_feed",
    "thebasics-product-feed": "feedcraft",
    "product-feed-manager": "wpfm_product_feed_manager",
    "wppfm": "wpfm_product_feed_manager",
    "google-listings-and-ads": "google_for_woocommerce",
}

FEED_FAMILY_MARKERS = {
    "ctx_feed_webappick": ("ctxfeed", "webappick", "woo_feed=", "woo-feed"),
    "adtribes_product_feed_pro": ("woo-product-feed-pro", "adtribes"),
    "woocommerce_google_product_feed": ("woocommerce_gpf", "woocommerce-google-product-feed"),
    "wpfm_product_feed_manager": ("wppfm", "wpfm", "product feed manager"),
    "google_for_woocommerce": ("google-listings-and-ads", "google for woocommerce"),
    "codesolz_feed": ("codesolz-feeds", "merchant-feed-booster"),
    "feedcraft": ("feedcraft-product-feed",),
}

DENY_FEED_SLUGS = {
    "instagram-feed",
    "facebook-for-woocommerce",
    "advanced-ads",
    "feedzy-rss-feeds",
}

PLUGIN_RE = re.compile(
    r"/wp-content/plugins/([^/?\\\"'#]+)(?:/[^?\\\"'#\\s<]*)?(?:[?&]ver=([^\\\"'&\\s<]+))?",
    re.I,
)

def challenge(text: str) -> bool:
    low = (text or "")[:30000].lower()
    return any(marker in low for marker in CHALLENGE_MARKERS)

def safe_origin(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"

def extract_plugins(text: str) -> list[dict]:
    found: dict[str, set[str]] = {}
    for m in PLUGIN_RE.finditer(text or ""):
        slug = re.sub(r"[^a-z0-9._-]", "", m.group(1).lower())
        if not slug:
            continue
        found.setdefault(slug, set())
        if m.group(2):
            found[slug].add(m.group(2))
    return [{"slug": s, "versions": sorted(v)} for s, v in sorted(found.items())]

def add_family(out: dict[str, list[dict]], family: str, evidence: str, confidence: str = "signal") -> None:
    bucket = out.setdefault(family, [])
    if not any(x["evidence"] == evidence for x in bucket):
        bucket.append({"evidence": evidence, "confidence": confidence})

def infer_families(
    plugin_assets: list[dict],
    namespaces: list[str],
    xhr: list[dict],
    api_urls: list[dict],
    text_markers: list[str],
) -> list[dict]:
    families: dict[str, list[dict]] = {}

    for item in plugin_assets:
        slug = item["slug"]
        if slug in KNOWN_FEED_SLUGS:
            add_family(families, KNOWN_FEED_SLUGS[slug], f"plugin_asset:{slug}", "strong")

    all_url_text = "\n".join(
        [str(x.get("url", "")) for x in xhr]
        + [str(x.get("url", "")) for x in api_urls]
        + [str(x) for x in text_markers]
    ).lower()
    ns_low = [str(x).lower() for x in namespaces]

    for family, markers in FEED_FAMILY_MARKERS.items():
        for marker in markers:
            if marker in all_url_text:
                add_family(families, family, f"public_endpoint_marker:{marker}", "signal")
    if any(x == "wpfm/v1" or x.startswith("wpfm/v1/") for x in ns_low):
        add_family(families, "wpfm_product_feed_manager", "wp_json_namespace:wpfm/v1", "strong")
    if any(x == "wppfm/v1" or x.startswith("wppfm/v1/") for x in ns_low):
        add_family(families, "wpfm_product_feed_manager", "wp_json_namespace:wppfm/v1", "strong")

    result = []
    for family, evidence in sorted(families.items()):
        if len(evidence) >= 2:
            conf = "strong"
        else:
            conf = evidence[0]["confidence"]
        result.append({"family": family, "confidence": conf, "evidence": evidence})
    return result

async def api_probe(request, url: str, label: str, method: str = "GET", timeout_ms: int = 10000) -> dict:
    try:
        response = await request.fetch(
            url,
            method=method,
            timeout=timeout_ms,
            max_redirects=5,
            headers={
                "accept": "application/json,text/plain;q=0.9,*/*;q=0.1",
                "user-agent": "Mozilla/5.0 (compatible; WooCommercePluginResearch/V175)",
            },
        )
        headers = response.headers
        body = b""
        if method == "GET":
            body = await response.body()
        return {
            "label": label,
            "method": method,
            "url": url,
            "status": int(response.status),
            "final_url": str(response.url),
            "content_type": headers.get("content-type", ""),
            "allow": headers.get("allow", ""),
            "content_length": headers.get("content-length", ""),
            "body_bytes": len(body),
            "challenge": challenge(body[:30000].decode("utf-8", "ignore")),
            # Deliberately do not persist GET response bodies for product endpoints.
            "body_persisted": False,
        }
    except PlaywrightTimeoutError:
        return {"label": label, "method": method, "url": url, "status": 0, "final_url": url,
                "content_type": "", "allow": "", "content_length": "", "body_bytes": 0,
                "challenge": False, "body_persisted": False, "transport": "timeout"}
    except Exception as exc:
        return {"label": label, "method": method, "url": url, "status": 0, "final_url": url,
                "content_type": "", "allow": "", "content_length": "", "body_bytes": 0,
                "challenge": False, "body_persisted": False, "transport": "error",
                "error": str(exc)[:240]}

async def inspect(name: str, root: str, pw) -> dict:
    root = root.rstrip("/")
    browser = await pw.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-dev-shm-usage"],
    )
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        ),
        locale="en-IN",
        viewport={"width": 1440, "height": 900},
        java_script_enabled=True,
    )
    page = await context.new_page()
    xhr: list[dict] = []
    seen_xhr: set[str] = set()

    def on_response(response) -> None:
        try:
            u = str(response.url or "")
            if u in seen_xhr:
                return
            resource = str(getattr(response, "request", None).resource_type or "")
            if resource not in {"xhr", "fetch"}:
                return
            ct = (response.headers or {}).get("content-type", "")
            interesting = (
                "wp-json" in u.lower()
                or "/api/" in u.lower()
                or "/wc/" in u.lower()
                or "wppfm" in u.lower()
                or "wpfm" in u.lower()
                or "feed" in u.lower()
                or "google" in u.lower()
                or "merchant" in u.lower()
                or "product" in u.lower()
                or "json" in ct.lower()
            )
            if not interesting:
                return
            seen_xhr.add(u)
            xhr.append({
                "url": u,
                "method": getattr(response.request, "method", ""),
                "status": int(response.status),
                "content_type": ct,
                "resource_type": resource,
            })
        except Exception:
            return

    page.on("response", on_response)

    result = {
        "schema_version": SCHEMA,
        "source_extractor_version": SOURCE_EXTRACTOR_VERSION,
        "site": name,
        "configured_root": root,
        "selected_origin": safe_origin(root),
        "browser": {},
        "public_endpoints": [],
        "woocommerce_rest_v1_v2_v3": [],
        "xhr": [],
        "plugin_assets": [],
        "feed_like_plugin_assets": [],
        "feed_family_signals": [],
        "public_api_namespaces": [],
        "rest_routes": [],
        "readme_metadata": [],
        "wordpress_generator": [],
        "identity_tokens": [],
        "status": "UNSET",
    }

    try:
        html = ""
        try:
            response = await page.goto(root, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(1800)
            html = await page.content()
            final_url = str(response.url) if response else root
            result["selected_origin"] = safe_origin(final_url)
            result["browser"] = {
                "status": int(response.status) if response else 0,
                "final_url": final_url,
                "challenge": challenge(html),
                "html_bytes": len(html),
            }
        except Exception as exc:
            result["browser"] = {
                "status": 0,
                "final_url": root,
                "challenge": False,
                "html_bytes": 0,
                "error": str(exc)[:240],
            }

        # Explicit public WordPress REST discovery.
        rest_specs = [
            ("/wp-json/", "wp-json-root"),
            ("/?rest_route=/", "rest-route-root"),
            ("/wp-json/wp/v2/", "wp-v2-root"),
            ("/?rest_route=/wp/v2/", "rest-route-wp-v2"),
        ]
        bodies: list[str] = [html]
        namespaces: list[str] = []
        route_keys: list[str] = []

        for path, label in rest_specs:
            url = result["selected_origin"].rstrip("/") + path
            probe = await api_probe(page.request, url, label, "GET", 10000)
            result["public_endpoints"].append(probe)
            if probe["status"] == 200:
                # Re-fetch only REST discovery bodies so namespace/route metadata can be parsed.
                try:
                    rr = await page.request.get(url, timeout=10000, max_redirects=5)
                    body = await rr.text()
                    if not challenge(body):
                        bodies.append(body)
                        if label in {"wp-json-root", "rest-route-root"}:
                            try:
                                data = json.loads(body)
                                namespaces.extend(str(x) for x in (data.get("namespaces") or []))
                                routes = data.get("routes") or {}
                                route_keys.extend(str(k) for k in routes.keys())
                            except Exception:
                                pass
                except Exception:
                    pass

        # WooCommerce REST v1/v2/v3 endpoint probes.
        for version in ("v1", "v2", "v3"):
            base = f"{result['selected_origin'].rstrip('/')}/wp-json/wc/{version}"
            root_probe = await api_probe(page.request, base + "/", f"wc-{version}-root", "GET", 9000)
            result["woocommerce_rest_v1_v2_v3"].append(root_probe)
            options_probe = await api_probe(page.request, base + "/products", f"wc-{version}-products-options", "OPTIONS", 9000)
            result["woocommerce_rest_v1_v2_v3"].append(options_probe)
            # Public endpoint probe only; response body is discarded.
            product_url = base + "/products?" + urlencode({"per_page": "1", "_fields": "id"})
            product_probe = await api_probe(page.request, product_url, f"wc-{version}-products-probe", "GET", 9000)
            result["woocommerce_rest_v1_v2_v3"].append(product_probe)

        # A general REST route probe catches plugin namespaces and admin-ajax existence.
        for path, label in (
            ("/wp-json/", "rest-general"),
            ("/wp-admin/admin-ajax.php?action=", "admin-ajax-surface"),
        ):
            url = result["selected_origin"].rstrip("/") + path
            result["public_endpoints"].append(await api_probe(page.request, url, label, "OPTIONS", 8000))

        # Common public catalog pages can expose plugin assets even when the homepage is sparse.
        page_htmls = [html]
        for page_path in ("/shop/", "/store/", "/products/"):
            u = result["selected_origin"].rstrip("/") + page_path
            try:
                rr = await page.goto(u, wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(600)
                ph = await page.content()
                if rr and rr.status == 200 and ph and not challenge(ph):
                    page_htmls.append(ph)
            except Exception:
                pass

        combined = "\n".join(page_htmls + bodies)
        assets = extract_plugins(combined)
        result["plugin_assets"] = assets
        result["feed_like_plugin_assets"] = [
            x["slug"] for x in assets
            if x["slug"] in KNOWN_FEED_SLUGS and x["slug"] not in DENY_FEED_SLUGS
        ]

        result["public_api_namespaces"] = sorted(set(namespaces))[:200]
        result["rest_routes"] = sorted(set(route_keys))[:200]
        result["xhr"] = sorted(xhr, key=lambda x: (x["url"], x["status"]))

        result["feed_family_signals"] = infer_families(
            assets,
            result["public_api_namespaces"],
            result["xhr"],
            result["public_endpoints"] + result["woocommerce_rest_v1_v2_v3"],
            [],
        )

        readme_targets = sorted(set(result["feed_like_plugin_assets"]))[:10]
        for slug in readme_targets:
            for filename in ("readme.txt", "README.md"):
                u = result["selected_origin"].rstrip("/") + "/wp-content/plugins/" + slug + "/" + filename
                p = await api_probe(page.request, u, f"readme:{slug}", "GET", 7000)
                if p["status"] == 200:
                    try:
                        rr = await page.request.get(u, timeout=7000, max_redirects=5)
                        body = await rr.text()
                        if body and not challenge(body):
                            result["readme_metadata"].append({
                                "slug": slug,
                                "file": filename,
                                "plugin_name": (re.search(r"^Plugin Name:\s*(.+)$", body, re.I | re.M) or [None, ""])[1].strip(),
                                "stable_tag": (re.search(r"^Stable tag:\s*(.+)$", body, re.I | re.M) or [None, ""])[1].strip(),
                            })
                    except Exception:
                        pass
                    break

        result["wordpress_generator"] = sorted(set(re.findall(
            r'<meta[^>]+(?:name|property)=[\"\']generator[\"\'][^>]+content=[\"\']([^\"\']+)',
            combined,
            re.I,
        )))[:30]

        host_token = re.sub(r"[^a-z0-9]+", " ", urlparse(root).hostname.lower()).split(".")[0]
        result["identity_tokens"] = sorted(set(
            [x for x in re.sub(r"[^a-z0-9]+", " ", name.lower()).split() if len(x) >= 2]
            + [x for x in re.sub(r"[^a-z0-9]+", " ", host_token.lower()).split() if len(x) >= 2]
        ))[:30]

        has_wc_api = any(
            p.get("status") in {200, 401, 403, 405}
            for p in result["woocommerce_rest_v1_v2_v3"]
            if "products" in p.get("label", "")
        )
        if result["feed_family_signals"]:
            result["status"] = "FEED_PLUGIN_SIGNALS_FOUND"
        elif result["plugin_assets"] or has_wc_api:
            result["status"] = "PLUGIN_SURFACE_RECOVERED_NO_FEED_SIGNAL"
        elif result["browser"].get("challenge"):
            result["status"] = "BROWSER_CHALLENGE_NO_PLUGIN_SURFACE"
        else:
            result["status"] = "NO_PLUGIN_SURFACE_RECOVERED"
    finally:
        try:
            await context.close()
        except Exception:
            pass
        try:
            await browser.close()
        except Exception:
            pass

    return result

async def main() -> None:
    wanted_name = os.environ.get("SITE_NAME", "").strip()
    wanted_root = os.environ.get("SITE_ROOT", "").strip()
    sites = [(wanted_name, wanted_root)] if wanted_name and wanted_root else SITES
    out_dir = Path(os.environ.get("OUT_DIR", "out/plugin-extraction-v175"))
    out_dir.mkdir(parents=True, exist_ok=True)
    site_timeout = float(os.environ.get("SITE_TIMEOUT", "240"))
    concurrency = int(os.environ.get("BROWSER_CONCURRENCY", "1" if len(sites) == 1 else "4"))

    async with async_playwright() as pw:
        sem = asyncio.Semaphore(concurrency)

        async def run_one(site):
            async with sem:
                try:
                    return await asyncio.wait_for(inspect(site[0], site[1], pw), timeout=site_timeout)
                except Exception as exc:
                    return {
                        "schema_version": SCHEMA,
                        "source_extractor_version": SOURCE_EXTRACTOR_VERSION,
                        "site": site[0],
                        "configured_root": site[1],
                        "selected_origin": site[1],
                        "status": "EXTRACTOR_ERROR",
                        "error": str(exc)[:300],
                    }

        results = await asyncio.gather(*(run_one(s) for s in sites))

    payload = {
        "schema_version": "woocommerce-22-plugin-extraction-v175/aggregate",
        "source_extractor_version": SOURCE_EXTRACTOR_VERSION,
        "site_count": len(results),
        "method_contract": [
            "Playwright browser rendering",
            "homepage XHR/fetch response URL capture",
            "WordPress WP-JSON root discovery",
            "WordPress REST wp/v2 discovery",
            "general REST surface / OPTIONS",
            "WooCommerce REST v1/v2/v3 root + product endpoint probes",
            "public plugin asset fingerprinting",
            "public plugin readme metadata",
        ],
        "policy": (
            "Public read-only plugin identification. WooCommerce product v1/v2/v3 requests are "
            "endpoint probes only; response bodies are discarded and never used for product extraction. "
            "No feed URL mining from XHR/HTML, no CAPTCHA solving, no Cloudflare challenge bypass, "
            "no clearance-cookie replay, no authentication bypass, no stealth/evasion."
        ),
        "results": sorted(results, key=lambda r: r["site"].lower()),
    }
    (out_dir / "aggregate.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# WooCommerce 22-site V175 plugin extraction",
        "",
        f"Coverage: {len(results)}/22",
        "",
        "| Site | Status | Feed family | WCF v1/v2/v3 | XHR records | Plugin assets |",
        "|---|---|---|---|---:|---:|",
    ]
    for r in payload["results"]:
        fam = ", ".join(x["family"] for x in r.get("feed_family_signals", [])) or "none"
        versions = ",".join(
            v for v in ("v1", "v2", "v3")
            if any(
                x.get("status") in {200, 401, 403, 405}
                for x in r.get("woocommerce_rest_v1_v2_v3", [])
                if x.get("label", "").startswith(f"wc-{v}-products")
            )
        ) or "none"
        lines.append(
            f'| {r["site"]} | {r["status"]} | {fam} | {versions} | '
            f'{len(r.get("xhr", []))} | {len(r.get("plugin_assets", []))} |'
        )
    (out_dir / "aggregate.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "site_count": len(results),
        "feed_signal_sites": sum(bool(r.get("feed_family_signals")) for r in results),
        "plugin_surface_sites": sum(bool(r.get("plugin_assets")) for r in results),
        "wc_api_probe_sites": sum(any(
            x.get("status") in {200,401,403,405} and "products" in x.get("label","")
            for x in r.get("woocommerce_rest_v1_v2_v3", [])
        ) for r in results),
        "xhr_signal_sites": sum(bool(r.get("xhr")) for r in results),
    }, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
