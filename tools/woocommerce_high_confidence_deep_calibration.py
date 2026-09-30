#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import importlib.util
import json
from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("wc_v175", ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)

MODULE.KNOWN_10 = set()

TARGETS = [
    ("PC Studio", "https://www.pcstudio.in", "woocommerce_google_product_feed"),
    ("Quickin Computers", "https://quickincomputers.com", "ctx_feed_webappick"),
    ("Avikaretails", "https://avikaretails.com", "adtribes_product_feed_pro"),
    ("IT Gadgets Online", "https://itgadgetsonline.com", "wpfm_product_feed_manager"),
    ("Geekbees", "https://geekbees.in", "google_for_woocommerce"),
    ("Ninja Dog", "https://ninjadog.in", "google_for_woocommerce"),
    ("Network IT Store", "https://networkitstore.in", "google_for_woocommerce"),
    ("My Nexus Infosys", "https://mynexusinfosys.com", "google_for_woocommerce"),
    ("Solanki Enterprises", "https://solankienterprises.com", "google_for_woocommerce"),
    ("AULA India", "https://aulaindia.com", "google_for_woocommerce"),
]

os.environ.setdefault("MAX_DIRECT_FEED_PROBES", "80")
os.environ.setdefault("MAX_INTERNAL_PAGES", "2")
os.environ.setdefault("PASSIVE_INDEX_ENABLED", "1")
os.environ.setdefault("WAYBACK_ENABLED", "1")
os.environ.setdefault("COMMONCRAWL_ENABLED", "0")
os.environ.setdefault("CF_BROWSER_RUN_ENABLED", "0")
os.environ.setdefault("BROWSERLESS_DIAGNOSTIC_ENABLED", "0")

async def run_target(name: str, root: str, expected: str, sem: asyncio.Semaphore) -> dict:
    async with sem:
        try:
            result = await MODULE.probe_site(name, root)
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
        result["expected_family"] = expected
        result["expected_family_match"] = result.get("family") == expected
        result["calibration_phase"] = "known_high_confidence_deep_10"
        print(json.dumps({
            "site": name,
            "expected_family": expected,
            "detected_family": result.get("family"),
            "family_confidence": result.get("family_confidence"),
            "native_verified": bool((result.get("native_feed") or {}).get("verified")),
            "candidate_count": result.get("candidate_count"),
            "elapsed_s": result.get("elapsed_s"),
            "probe_error": result.get("probe_error"),
        }), flush=True)
        return result

async def main() -> None:
    site_concurrency = max(1, min(len(TARGETS), int(os.getenv("SITE_CONCURRENCY", "5"))))
    sem = asyncio.Semaphore(site_concurrency)
    results = list(await asyncio.gather(
        *(run_target(name, root, expected, sem) for name, root, expected in TARGETS)
    ))

    learning = []
    for r in results:
        feed = r.get("native_feed") or {}
        tried = feed.get("tried") or []
        learning.append({
            "site": r["site"],
            "expected_family": r["expected_family"],
            "detected_family": r.get("family"),
            "family_confidence": r.get("family_confidence"),
            "family_match": r.get("expected_family_match"),
            "native_verified": bool(feed.get("verified")),
            "native_url": feed.get("url"),
            "item_count": feed.get("item_count", 0),
            "candidate_count": r.get("candidate_count", 0),
            "browser_engines": [
                {
                    "engine": b.get("engine"),
                    "status": b.get("status"),
                    "challenge": b.get("challenge"),
                    "xhr_count": len(b.get("xhr_urls") or []),
                    "resource_count": len(b.get("resource_urls") or []),
                    "plugin_assets": b.get("plugin_asset_slugs") or [],
                    "namespaces": b.get("namespaces") or [],
                }
                for b in (r.get("browser") or [])
            ],
            "explicit_feed_candidates": r.get("explicit_feed_candidates") or [],
            "query_feed_candidates": r.get("query_feed_candidates") or [],
            "directory_candidates": (r.get("passive_discovery") or {}).get("directory_candidates") or [],
            "historical_candidate_urls": (r.get("passive_discovery") or {}).get("historical_candidate_urls") or [],
            "tried_sample": tried[:80],
            "probe_error": r.get("probe_error"),
        })

    summary = {
        "schema": "woocommerce-high-confidence-deep-calibration/v2",
        "targets": [x[0] for x in TARGETS],
        "target_count": len(TARGETS),
        "standalone_feed_generator_count": 4,
        "google_for_woocommerce_count": 6,
        "native_verified": sum(1 for r in results if (r.get("native_feed") or {}).get("verified")),
        "family_matches": sum(1 for r in results if r.get("expected_family_match")),
        "probe_errors": sum(1 for r in results if r.get("probe_error")),
        "learning": learning,
        "results": results,
    }
    out = ROOT / "out" / "woocommerce-high-confidence-deep-calibration"
    out.mkdir(parents=True, exist_ok=True)
    (out / "phase1b.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# WooCommerce High-Confidence Deep Calibration — Phase 1 (10 Sites)",
        "",
        "| Site | Expected family | Detected family | Confidence | Native feed | Candidates | Error |",
        "|---|---|---|---|---|---:|---|",
    ]
    for r in results:
        feed = r.get("native_feed") or {}
        lines.append(
            f"| {r['site']} | {r['expected_family']} | {r.get('family')} | "
            f"{r.get('family_confidence')} | {'YES' if feed.get('verified') else 'NO'} | "
            f"{r.get('candidate_count', 0)} | {r.get('probe_error', '')} |"
        )
    lines += ["", "## Learning", ""]
    for item in learning:
        lines.append(f"### {item['site']}")
        lines.append(f"- family_match={item['family_match']}")
        lines.append(f"- native_verified={item['native_verified']}")
        lines.append(f"- explicit_feed_candidates={len(item['explicit_feed_candidates'])}")
        lines.append(f"- query_feed_candidates={len(item['query_feed_candidates'])}")
        lines.append(f"- directory_candidates={len(item['directory_candidates'])}")
        lines.append(f"- historical_candidate_urls={len(item['historical_candidate_urls'])}")
        lines.append(f"- browser_engines={len(item['browser_engines'])}")
    (out / "phase1b.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

if __name__ == "__main__":
    asyncio.run(main())
