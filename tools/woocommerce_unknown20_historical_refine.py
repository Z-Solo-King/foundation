#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import importlib.util
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "wc_v175_historical_refine",
    ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

MODULE.KNOWN_10 = set()

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

os.environ.setdefault("MAX_DIRECT_FEED_PROBES", "100")
os.environ.setdefault("MAX_INTERNAL_PAGES", "2")
os.environ.setdefault("PASSIVE_INDEX_ENABLED", "1")
os.environ.setdefault("WAYBACK_ENABLED", "1")
os.environ.setdefault("COMMONCRAWL_ENABLED", "0")
os.environ.setdefault("CF_BROWSER_RUN_ENABLED", "0")
os.environ.setdefault("BROWSERLESS_DIAGNOSTIC_ENABLED", "0")

FEED_HINT = re.compile(
    r"(?:feed|google|merchant|shopping|woocommerce_gpf|woo_feed|wpfm|webtoffee|"
    r"adtribes|feedcraft|product-feed|product_feed|merchantcenter)",
    re.I,
)
PLUGIN_HINT = re.compile(r"/wp-content/plugins/([^/?#\"' <]+)/", re.I)

def host(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")

def same_host(a: str, b: str) -> bool:
    return host(a) == host(b)

def path_of(url: str) -> str:
    return (urlsplit(url).path or "/").lower()

def is_rss(url: str) -> bool:
    p = path_of(url)
    return p.endswith("/feed/") or p.endswith("/feed.xml") or "/comments/feed" in p or re.search(r"/(?:author|tag|category|product-category|brands?|manufacturer)/[^/]+/feed/?$", p)

def discover_urls(text: str, root: str) -> list[str]:
    out = set()
    raw_text = str(text or "")
    for raw in re.findall(r"https?://[^\s\"'<>]+", raw_text, re.I):
        u = raw.rstrip("),.;")
        if same_host(u, root) and FEED_HINT.search(u) and not is_rss(u):
            out.add(u)
    for raw in re.findall(r'''(?:href|src|loc|data-href|data-url|feedUrl|feed_url|product_feed|google_feed)\s*[:=]\s*[\"']([^\"']+)[\"']''', raw_text, re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and FEED_HINT.search(u) and not is_rss(u):
            out.add(u)
    for raw in re.findall(r'''(?:wp-content/uploads/[^\s\"'<>]+\.xml(?:\.gz)?(?:[?#][^\s\"'<>]*)?)''', raw_text, re.I):
        u = urljoin(root + "/", "/" + raw.lstrip("/"))
        if same_host(u, root) and not is_rss(u):
            out.add(u)
    return sorted(out)[:240]

def plugin_slugs(text: str) -> list[str]:
    return sorted(set(PLUGIN_HINT.findall(text or "")))[:120]

def plugin_families(slugs: list[str], text: str) -> dict[str, list[str]]:
    blobs = "\n".join([str(text or "")] + slugs).lower()
    hits = MODULE.find_plugin_hits([blobs], slugs, MODULE.parse_namespaces(blobs))
    return {k: v for k, v in hits.items()}

async def wayback_cdx(root: str, url_filter: str, limit: int = 30) -> list[dict]:
    pattern = quote(host(root) + "/*", safe="")
    filter_expr = quote(url_filter, safe="")
    api = (
        "https://web.archive.org/cdx/search/cdx?url=" + pattern +
        "&output=json&fl=timestamp,original,statuscode,mimetype,digest" +
        "&filter=statuscode:200&filter=urlkey:" + filter_expr +
        "&collapse=urlkey&limit=" + str(limit)
    )
    try:
        import httpx
        async with httpx.AsyncClient(
            headers={"User-Agent": "Mozilla/5.0 (compatible; WooCommerceHistoricalRefine/2026.09)"},
            timeout=25,
            follow_redirects=True,
        ) as client:
            r = await client.get(api)
            if r.status_code != 200:
                return []
            data = r.json()
            rows = data[1:] if isinstance(data, list) and data and isinstance(data[0], list) else data
            out = []
            for row in rows or []:
                if isinstance(row, list) and len(row) >= 3:
                    out.append({
                        "timestamp": str(row[0]),
                        "original": str(row[1]),
                        "status": str(row[2]),
                        "mimetype": str(row[3]) if len(row) > 3 else "",
                        "digest": str(row[4]) if len(row) > 4 else "",
                    })
            return out
    except Exception:
        return []

async def fetch_snapshots(root: str) -> dict:
    feed_rows, plugin_rows = await asyncio.gather(
        wayback_cdx(root, ".*(feed|google|merchant|shopping|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed|product_feed).*", 40),
        wayback_cdx(root, ".*wp-content/plugins/.*", 40),
    )
    rows = []
    seen = set()
    for row in feed_rows + plugin_rows:
        key = (row["timestamp"], row["original"])
        if key not in seen and row["original"] not in {x["original"] for x in rows}:
            seen.add(key)
            rows.append(row)
    rows = sorted(rows, key=lambda x: (0 if FEED_HINT.search(x["original"]) else 1, x["original"]))[:32]

    import httpx
    texts = []
    async with httpx.AsyncClient(
        headers={"User-Agent": "Mozilla/5.0 (compatible; WooCommerceHistoricalRefine/2026.09)"},
        timeout=20,
        follow_redirects=True,
    ) as client:
        sem = asyncio.Semaphore(6)
        async def one(row):
            async with sem:
                snap = f"https://web.archive.org/web/{row['timestamp']}id_/{row['original']}"
                try:
                    r = await client.get(snap)
                    if r.status_code == 200 and r.text:
                        return row, r.text[:700_000]
                except Exception:
                    pass
                return row, ""
        results = await asyncio.gather(*(one(r) for r in rows))
    for row, text in results:
        if text:
            texts.append({"snapshot": row, "text": text})
    return {
        "cdx_rows": rows,
        "snapshot_count": len(texts),
        "snapshots": texts,
    }

async def current_probe(root: str, candidates: list[str]) -> dict:
    return await MODULE.direct_feed_probe(root, candidates, "Mozilla/5.0 (compatible; WooCommerceHistoricalRefine/2026.09)")

async def run_target(name: str, root: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        base = await MODULE.probe_site(name, root)
        hist = await fetch_snapshots(root)
        recovered = set(base.get("explicit_feed_candidates") or [])
        recovered.update(base.get("query_feed_candidates") or [])
        historical_urls = set()
        historical_slugs = set(base.get("plugin_asset_slugs") or [])
        historical_namespaces = set(base.get("namespaces") or [])
        historical_family_hits: dict[str, set[str]] = {}
        for snap in hist["snapshots"]:
            txt = snap["text"]
            for u in discover_urls(txt, root):
                historical_urls.add(u)
            for s in plugin_slugs(txt):
                historical_slugs.add(s)
            ns = MODULE.parse_namespaces(txt)
            historical_namespaces.update(ns)
            for fam, values in plugin_families(list(historical_slugs), txt).items():
                historical_family_hits.setdefault(fam, set()).update(values)

        current_candidates = sorted(historical_urls)
        current_feed = await current_probe(root, current_candidates[:100]) if current_candidates else {
            "verified": False, "url": None, "item_count": 0, "sha256": "", "tried": []
        }

        combined_families = MODULE.find_plugin_hits(
            [json.dumps(base.get("xhr_urls") or []), "\n".join(s["text"] for s in hist["snapshots"][:12])],
            sorted(historical_slugs),
            sorted(historical_namespaces),
        )
        for fam, hits in historical_family_hits.items():
            combined_families.setdefault(fam, [])
            combined_families[fam] = sorted(set(combined_families[fam]) | set(hits))
        top_family = None
        top_confidence = "low"
        if combined_families:
            top_family = sorted(combined_families, key=lambda k: (-len(combined_families[k]), k))[0]
            current_families = MODULE.find_plugin_hits(
                [json.dumps(base.get("xhr_urls") or [])],
                base.get("plugin_asset_slugs") or [],
                base.get("namespaces") or [],
            )
            if top_family in current_families:
                top_confidence = MODULE.plugin_family_confidence(
                    current_families,
                    base.get("plugin_asset_slugs") or [],
                    base.get("namespaces") or [],
                )
            else:
                top_confidence = "low"

        result = {
            "site": name,
            "url": root,
            "baseline_family": base.get("family"),
            "baseline_family_confidence": base.get("family_confidence"),
            "refined_family": top_family or base.get("family"),
            "refined_family_confidence": top_confidence if top_family else base.get("family_confidence"),
            "baseline_native_verified": bool((base.get("native_feed") or {}).get("verified")),
            "historical_native_verified": bool(current_feed.get("verified")),
            "native_feed": current_feed if current_feed.get("verified") else (base.get("native_feed") or {}),
            "baseline_candidate_count": base.get("candidate_count"),
            "historical_candidate_count": len(historical_urls),
            "historical_snapshot_count": hist["snapshot_count"],
            "historical_plugin_slugs": sorted(historical_slugs)[:120],
            "historical_namespaces": sorted(historical_namespaces)[:160],
            "historical_family_hits": {k: sorted(v)[:30] for k, v in sorted(historical_family_hits.items())},
            "historical_feed_candidates": sorted(historical_urls)[:120],
            "historical_tried": (current_feed.get("tried") or [])[:100],
            "browser": base.get("browser") or [],
            "challenge_encountered": bool(base.get("challenge_encountered")),
            "feed_transport": "standalone_xml_candidate_probe",
            "elapsed_s": base.get("elapsed_s"),
        }
        print(json.dumps({
            "site": name,
            "baseline_family": result["baseline_family"],
            "refined_family": result["refined_family"],
            "refined_confidence": result["refined_family_confidence"],
            "historical_snapshots": result["historical_snapshot_count"],
            "historical_candidates": result["historical_candidate_count"],
            "native_verified": bool(result["native_feed"].get("verified")),
        }), flush=True)
        return result

async def main() -> None:
    shard = int(os.getenv("SHARD", "1"))
    shards = int(os.getenv("SHARDS", "6"))
    selected = [x for i, x in enumerate(TARGETS) if i % shards + 1 == shard]
    sem = asyncio.Semaphore(max(1, min(len(selected), int(os.getenv("SITE_CONCURRENCY", "2")))))
    results = list(await asyncio.gather(*(run_target(name, root, sem) for name, root in selected)))
    out = ROOT / "out" / "woocommerce-unknown20-historical-refine"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"shard-{shard}.json").write_text(
        json.dumps({
            "schema": "woocommerce-unknown20-historical-refine/v1",
            "shard": shard,
            "shards": shards,
            "targets": [n for n, _ in selected],
            "results": results,
        }, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

if __name__ == "__main__":
    asyncio.run(main())
