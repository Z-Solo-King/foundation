#!/usr/bin/env python3
"""
WooCommerce 21-site plugin-channel extractor.

Evidence channels:
  1. Playwright homepage + browser XHR/Fetch response URLs and metadata.
  2. WP-JSON root / REST root.
  3. WooCommerce REST API v1/v2/v3 route probes.
  4. Generic REST endpoint probes.
  5. Homepage HTML/plugin assets.

This lane is metadata-first: product payload bodies are not persisted.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

VERSION = "V175-channel-contract-v1"

SITES = [
    ("AULA India","https://aulaindia.com"),
    ("Aarna Computers","https://aarnacomputers.com"),
    ("Ads Store","https://adsstore.in"),
    ("Cosmic Byte","https://www.thecosmicbyte.com"),
    ("EZPZ Solutions","https://www.ezpzsolutions.in"),
    ("KC Computers","https://kccomputers.co.in"),
    ("KRG KART","https://krgkart.com"),
    ("Kryptronix Gaming","https://kryptronix.in"),
    ("Meckeys","https://meckeys.com"),
    ("Moskeys","https://moskeys.com"),
    ("NCL Computer","https://nclcomputer.com"),
    ("PC Kumar Infotech","https://pckumar.in"),
    ("PCHubShop","https://www.pchubshop.com"),
    ("Prime ABGB","https://www.primeabgb.com"),
    ("SCL Gaming","https://sclgaming.in"),
    ("StacksKB","https://stackskb.com"),
    ("Theproaudio","https://www.theproaudio.com"),
    ("Variety Infotech","https://varietyinfotech.com"),
    ("Viper PC","https://viperpc.in"),
    ("hotshiftpc","https://hotshiftpc.com"),
    ("ithunt","https://ithunt.in"),
]

CHALLENGE_MARKERS = (
    "just a moment","cf-chl-","cf-browser-verification","cf-mitigated",
    "managed_challenge","attention required","checking your browser",
    "enable javascript and cookies","verify you are human","cf-turnstile",
    "captcha","challenge-platform",
)

KNOWN_FEED_PLUGINS = {
    "woocommerce-google-product-feed":"woocommerce_google_product_feed",
    "woo-feed":"ctx_feed_webappick",
    "webappick-product-feed-for-woocommerce":"ctx_feed_webappick",
    "ctx-feed":"ctx_feed_webappick",
    "woo-product-feed-pro":"adtribes_product_feed_pro",
    "merchant-feed-booster-lite-for-woocommerce":"codesolz_feed",
    "thebasics-product-feed":"feedcraft",
    "product-feed-manager":"wpfm_product_feed_manager",
    "wppfm":"wpfm_product_feed_manager",
    "google-listings-and-ads":"google_for_woocommerce",
}

PLUGIN_DENY = re.compile(
    r"^(?:instagram-feed|facebook-for-woocommerce|advanced-ads|feedzy-rss-feeds)$", re.I
)

def challenge(text: str) -> bool:
    low = (text or "")[:30000].lower()
    return any(m in low for m in CHALLENGE_MARKERS)

def plugin_assets(text: str):
    found = {}
    rx = re.compile(r"/wp-content/plugins/([^/?\"'#\\]+)(?:/[^?\"'#\\\s<]*)?", re.I)
    for m in rx.finditer(text or ""):
        slug = re.sub(r"[^a-z0-9._-]", "", m.group(1).lower())
        if slug and slug not in found:
            found[slug] = []
    return [{"slug": s, "versions": found[s]} for s in sorted(found)]

def feed_signals(assets, namespaces, xhr_urls, html):
    evidence = {}
    low = (html or "").lower()
    all_tokens = set(a["slug"] for a in assets)
    all_tokens.update(str(x).lower() for x in namespaces)
    all_tokens.update(str(x).lower() for x in xhr_urls)
    for slug, family in KNOWN_FEED_PLUGINS.items():
        ev = []
        if slug in all_tokens:
            if any(a["slug"] == slug for a in assets): ev.append(f"plugin_asset:{slug}")
            if any(slug in str(n).lower() for n in namespaces): ev.append(f"namespace:{slug}")
            if any(slug in str(u).lower() for u in xhr_urls): ev.append(f"xhr_url:{slug}")
            if slug in low: ev.append(f"html_marker:{slug}")
        if ev:
            evidence.setdefault(family, []).extend(ev)
    for family, markers in {
        "ctx_feed_webappick": ("ctxfeed","webappick","woo_feed="),
        "adtribes_product_feed_pro": ("woo-product-feed-pro","adtribes"),
        "woocommerce_google_product_feed": ("woocommerce_gpf","woocommerce-google-product-feed"),
        "google_for_woocommerce": ("google-listings-and-ads","google for woocommerce"),
        "wpfm_product_feed_manager": ("wpfm/v1","wppfm/v1","wpfm"),
    }.items():
        ev = []
        for marker in markers:
            if any(marker in str(x).lower() for x in (namespaces + xhr_urls)):
                ev.append(f"public_surface:{marker}")
            elif marker in low:
                ev.append(f"html_marker:{marker}")
        if ev:
            evidence.setdefault(family, []).extend(ev)
    return [
        {"family": fam, "confidence": "strong" if len(set(ev)) >= 2 else "signal",
         "evidence": sorted(set(ev))}
        for fam, ev in sorted(evidence.items())
    ]

async def request_meta(req, url: str, timeout_ms: int = 10000):
    try:
        r = await req.get(url, timeout=timeout_ms, max_redirects=5, headers={
            "accept":"application/json,text/plain,text/html;q=.8,*/*;q=.1",
            "user-agent":"Mozilla/5.0 (compatible; WooCommercePluginChannelResearch/V175)",
        })
        status = int(r.status)
        ct = r.headers.get("content-type","")
        # Do not persist product response payloads. Only inspect a small prefix for API schema markers.
        body = ""
        if "json" in ct.lower() or "text" in ct.lower() or "xml" in ct.lower():
            try:
                body = (await r.text())[:5000]
            except Exception:
                body = ""
        return {
            "status": status,
            "final_url": str(r.url),
            "content_type": ct,
            "bytes": len(body),
            "challenge": challenge(body),
            "route_markers": sorted(set(re.findall(
                r"(?:wpfm|wppfm|feed|google|merchant|woocommerce|product-feed|webappick|adtribes)",
                body, re.I
            )))[:40],
        }
    except PWTimeout:
        return {"status":0,"final_url":url,"content_type":"","bytes":0,"challenge":False,"transport":"timeout","route_markers":[]}
    except Exception as exc:
        return {"status":0,"final_url":url,"content_type":"","bytes":0,"challenge":False,
                "transport":"error","route_markers":[],"error":str(exc)[:200]}

async def inspect(name, root, sem):
    async with sem:
        root = root.rstrip("/")
        browser = await sem._loop.run_in_executor(None, lambda: None) if False else None
        out = {
            "schema_version":"woocommerce-21-plugin-channel-extraction/v1",
            "source_extractor_version":VERSION,
            "site":name,
            "configured_root":root,
            "selected_origin":root,
            "channels":{
                "browser_homepage":{"status":0,"final_url":root,"challenge":False,"html_bytes":0,"xhr_count":0,"xhr":[]},
                "homepage_html":{"status":0,"bytes":0},
                "wp_json":{},
                "rest_api":{},
                "wc_api":{},
            },
        }
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
                locale="en-IN", viewport={"width":1440,"height":900}, java_script_enabled=True
            )
            page = await context.new_page()
            xhr = []
            seen = set()

            async def on_response(resp):
                try:
                    u = str(resp.url)
                    if u in seen or not u.startswith(("http://","https://")): return
                    req = resp.request
                    resource = str(req.resource_type or "")
                    if resource not in ("xhr","fetch") and not re.search(r"(wp-json|wc/|feed|google|merchant|product-feed)",u,re.I):
                        return
                    seen.add(u)
                    ct = resp.headers.get("content-type","")
                    xhr.append({
                        "url":u,
                        "method":req.method,
                        "status":int(resp.status),
                        "content_type":ct,
                        "resource_type":resource,
                        "same_origin": (urlparse(u).hostname or "").lower().replace("www.","") == (urlparse(root).hostname or "").lower().replace("www.",""),
                    })
                except Exception:
                    return

            page.on("response", on_response)
            html = ""
            try:
                r = await page.goto(root, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(2500)
                html = await page.content()
                final = str(r.url) if r else root
                out["selected_origin"] = f"{urlparse(final).scheme}://{urlparse(final).netloc}"
                out["channels"]["browser_homepage"].update({
                    "status": int(r.status) if r else 0,
                    "final_url": final,
                    "challenge": challenge(html),
                    "html_bytes": len(html),
                    "xhr_count": len(xhr),
                    "xhr": sorted(xhr, key=lambda x:x["url"])[:250],
                })
                out["channels"]["homepage_html"]={"status":int(r.status) if r else 0,"bytes":len(html),"challenge":challenge(html)}
            except Exception as exc:
                out["channels"]["browser_homepage"]["error"] = str(exc)[:240]

            # Direct public API/REST metadata probes.
            origin = out["selected_origin"].rstrip("/")
            probe_paths = [
                ("/wp-json/","wp_json_root"),
                ("/?rest_route=/","rest_root_query"),
                ("/wp-json/wp/v2/","wp_v2_root"),
                ("/wp-json/wc/","wc_rest_root"),
                ("/wp-json/wc/v1/","wc_v1_root"),
                ("/wp-json/wc/v2/","wc_v2_root"),
                ("/wp-json/wc/v3/","wc_v3_root"),
                ("/?rest_route=/wc/v1/","wc_v1_rest_query"),
                ("/?rest_route=/wc/v2/","wc_v2_rest_query"),
                ("/?rest_route=/wc/v3/","wc_v3_rest_query"),
            ]
            for path, key in probe_paths:
                z = await request_meta(page.request, origin + path, 10000)
                if key.startswith("wc_v"):
                    out["channels"]["wc_api"][key] = {k:z[k] for k in z if k!="route_markers"} | {
                        "route_markers":z.get("route_markers",[])
                    }
                elif key.startswith("rest"):
                    out["channels"]["rest_api"][key] = z
                else:
                    out["channels"]["wp_json"][key] = z

            # Extract namespaces from the WP-JSON root without persisting its body.
            ns = set()
            z = out["channels"]["wp_json"].get("wp_json_root", {})
            root_url = origin + "/wp-json/"
            root_probe = await request_meta(page.request, root_url, 10000)
            if root_probe["status"] == 200:
                try:
                    rr = await page.request.get(root_url, timeout=10000)
                    data = await rr.json()
                    if isinstance(data.get("namespaces"), list):
                        ns.update(map(str, data["namespaces"]))
                    for k in data.keys():
                        if re.search(r"feed|google|merchant|product|wpfm|woo", str(k), re.I):
                            ns.add(str(k))
                except Exception:
                    pass

            assets = plugin_assets(html)
            xhr_urls = [x["url"] for x in xhr]
            families = feed_signals(assets, sorted(ns), xhr_urls, html)
            feed_like = [
                a["slug"] for a in assets
                if not PLUGIN_DENY.match(a["slug"]) and (
                    a["slug"] in KNOWN_FEED_PLUGINS or
                    bool(re.search(r"(^|[-_])(product-feed|merchant-feed|shopping-feed|google-product-feed)([-_]|$)",a["slug"],re.I))
                )
            ]
            wc_states = list(out["channels"]["wc_api"].values())
            out.update({
                "plugin_assets":assets,
                "feed_like_plugin_assets":feed_like,
                "feed_family_signals":families,
                "public_api_namespaces":sorted(ns)[:200],
                "identity_tokens":sorted(set(
                    re.sub(r"[^a-z0-9]+"," ",name.lower()).split()+
                    re.sub(r"[^a-z0-9]+"," ",(urlparse(root).hostname or "").lower()).split()
                ))[:30],
                "status":(
                    "FEED_PLUGIN_SIGNALS_FOUND" if families or feed_like else
                    "BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE" if challenge(html) else
                    "PLUGIN_SURFACE_EXTRACTED" if assets else
                    "PUBLIC_SURFACE_REACHED_NO_PLUGIN_ASSETS"
                ),
                "wc_api_summary":{
                    "v1_reachable": any(v.get("status")==200 for k,v in out["channels"]["wc_api"].items() if "v1" in k),
                    "v2_reachable": any(v.get("status")==200 for k,v in out["channels"]["wc_api"].items() if "v2" in k),
                    "v3_reachable": any(v.get("status")==200 for k,v in out["channels"]["wc_api"].items() if "v3" in k),
                    "v1_statuses":sorted(set(v.get("status",0) for k,v in out["channels"]["wc_api"].items() if "v1" in k)),
                    "v2_statuses":sorted(set(v.get("status",0) for k,v in out["channels"]["wc_api"].items() if "v2" in k)),
                    "v3_statuses":sorted(set(v.get("status",0) for k,v in out["channels"]["wc_api"].items() if "v3" in k)),
                },
            })
            await context.close()
            await browser.close()
        return out

async def main():
    target_name=os.environ.get("SITE_NAME","").strip()
    target_root=os.environ.get("SITE_ROOT","").strip()
    sites=[(target_name,target_root)] if target_name and target_root else SITES
    concurrency=max(1,int(os.environ.get("SITE_CONCURRENCY","4")))
    sem=asyncio.Semaphore(concurrency)
    results=await asyncio.gather(*(inspect(n,u,sem) for n,u in sites))
    outdir=Path(os.environ.get("OUT_DIR","out/plugin-channel-extract"))
    outdir.mkdir(parents=True,exist_ok=True)
    payload={
        "schema_version":"woocommerce-21-plugin-channel-extraction-aggregate/v1",
        "source_extractor_version":VERSION,
        "site_count":len(results),
        "contract":"Playwright homepage/XHR + WP-JSON + generic REST + WooCommerce REST v1/v2/v3. Metadata-first; product payload bodies are not retained.",
        "results":sorted(results,key=lambda x:x["site"].lower()),
    }
    (outdir/"aggregate.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    rows=["# WooCommerce 21-site plugin channel extraction","","| Site | Status | Feed families | WC v1 | WC v2 | WC v3 | XHR count | Plugins |","|---|---|---|---|---|---|---:|---:|"]
    for r in payload["results"]:
        rows.append(
            f'| {r["site"]} | {r["status"]} | {", ".join(x["family"] for x in r.get("feed_family_signals",[])) or "none"} | '
            f'{r["wc_api_summary"]["v1_statuses"]} | {r["wc_api_summary"]["v2_statuses"]} | {r["wc_api_summary"]["v3_statuses"]} | '
            f'{r["channels"]["browser_homepage"].get("xhr_count",0)} | {len(r.get("plugin_assets",[]))} |'
        )
    (outdir/"aggregate.md").write_text("\n".join(rows)+"\n",encoding="utf-8")
    print(json.dumps({
        "site_count":len(results),
        "feed_signal_sites":sum(bool(r.get("feed_family_signals") or r.get("feed_like_plugin_assets")) for r in results),
        "plugin_surface_sites":sum(bool(r.get("plugin_assets")) for r in results),
        "xhr_reached_sites":sum(r["channels"]["browser_homepage"].get("xhr_count",0)>0 for r in results),
        "wc_v1_200":sum(r["wc_api_summary"]["v1_reachable"] for r in results),
        "wc_v2_200":sum(r["wc_api_summary"]["v2_reachable"] for r in results),
        "wc_v3_200":sum(r["wc_api_summary"]["v3_reachable"] for r in results),
    },indent=2))

if __name__=="__main__":
    asyncio.run(main())
