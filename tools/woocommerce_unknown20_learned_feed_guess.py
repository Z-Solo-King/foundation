#!/usr/bin/env python3
from __future__ import annotations
import asyncio
import importlib.util
import json
import os
from pathlib import Path
import sys
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
CAL = Path(os.getenv("CALIBRATION_JSON", ROOT / "phase1b.json"))

KNOWN_PHASE1 = {
    "pcstudio.in", "quickincomputers.com", "avikaretails.com", "itgadgetsonline.com",
    "geekbees.in", "ninjadog.in", "networkitstore.in", "mynexusinfosys.com",
    "solankienterprises.com", "aulaindia.com",
}
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

SPEC = importlib.util.spec_from_file_location(
    "wc_v175_unknown20",
    ROOT / "tools" / "woocommerce_v175_plugin_fingerprint_22.py",
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)
MODULE.KNOWN_10 = set(KNOWN_PHASE1)

def host_of(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")

def rel_url(url: str, known_root: str) -> str | None:
    try:
        u = urlsplit(url)
        if host_of(url) != host_of(known_root):
            return None
        return urlunsplit(("", "", u.path or "/", u.query, ""))
    except Exception:
        return None

def add_transfer_candidate(target: set[str], rel: str) -> None:
    low = rel.lower()
    if any(k in low for k in ("woocommerce_gpf=", "woo_feed=")):
        target.add(rel)
        return
    if low.startswith("/wp-json/") and any(k in low for k in ("feedcraft", "google-feed", "google-product-feed", "woo-feed")):
        target.add(rel)
        return
    stable_names = {
        "google.xml", "google-shopping.xml", "google-shopping-feed.xml",
        "google-products.xml", "google-feed.xml", "wt_google_feed.xml",
        "wt_google_feed.xml.gz", "google-products.xml.gz",
    }
    base = Path(urlsplit(rel).path).name.lower()
    if base in stable_names:
        target.add(rel)

def derive_learning(calibration: dict) -> dict:
    by_family: dict[str, set[str]] = {}
    global_transfer: set[str] = set()
    directories: set[str] = set()
    evidence = []
    for item in calibration.get("learning") or []:
        family = str(item.get("expected_family") or item.get("detected_family") or "unknown_woocommerce")
        known_root = ""
        for name, root in [
            ("PC Studio", "https://www.pcstudio.in"),
            ("Quickin Computers", "https://quickincomputers.com"),
            ("Avikaretails", "https://avikaretails.com"),
            ("IT Gadgets Online", "https://itgadgetsonline.com"),
            ("Geekbees", "https://geekbees.in"),
            ("Ninja Dog", "https://ninjadog.in"),
            ("Network IT Store", "https://networkitstore.in"),
            ("My Nexus Infosys", "https://mynexusinfosys.com"),
            ("Solanki Enterprises", "https://solankienterprises.com"),
            ("AULA India", "https://aulaindia.com"),
        ]:
            if name == item.get("site"):
                known_root = root
                break
        fam = by_family.setdefault(family, set())
        for key in ("query_feed_candidates", "explicit_feed_candidates"):
            for raw in item.get(key) or []:
                rel = rel_url(str(raw), known_root) if known_root else None
                if rel:
                    add_transfer_candidate(fam, rel)
                    add_transfer_candidate(global_transfer, rel)
        for raw in item.get("directory_candidates") or []:
            rel = rel_url(str(raw), known_root) if known_root else None
            if rel:
                path = urlsplit(rel).path or "/"
                if not path.endswith("/"):
                    path = path.rsplit("/", 1)[0] + "/"
                directories.add(path)
        evidence.append({
            "site": item.get("site"),
            "expected_family": family,
            "family_match": bool(item.get("family_match")),
            "native_verified": bool(item.get("native_verified")),
            "query_count": len(item.get("query_feed_candidates") or []),
            "directory_count": len(item.get("directory_candidates") or []),
            "historical_count": len(item.get("historical_candidate_urls") or []),
        })
    # Stable, observed transfer paths are added to plugin-specific and generic lanes.
    for family, paths in by_family.items():
        MODULE.PLUGIN_CANDIDATES.setdefault(family, [])
        MODULE.PLUGIN_CANDIDATES[family].extend(sorted(paths))
    MODULE.GENERIC_FEED_PATHS.extend(sorted(global_transfer))
    MODULE.GENERIC_FEED_PATHS = list(dict.fromkeys(MODULE.GENERIC_FEED_PATHS))
    MODULE.PLUGIN_FEED_DIRECTORIES.extend(sorted(directories))
    MODULE.PLUGIN_FEED_DIRECTORIES = list(dict.fromkeys(MODULE.PLUGIN_FEED_DIRECTORIES))
    return {
        "schema": "woocommerce-unknown20-learned-transfer/v1",
        "families": {k: sorted(v) for k, v in sorted(by_family.items())},
        "global_transfer_paths": sorted(global_transfer),
        "learned_directories": sorted(directories),
        "evidence": evidence,
    }

async def main() -> None:
    calibration = json.loads(CAL.read_text(encoding="utf-8"))
    transfer = derive_learning(calibration)
    shard = int(os.getenv("SHARD", "1"))
    shards = int(os.getenv("SHARDS", "6"))
    selected = [x for i, x in enumerate(TARGETS) if i % shards + 1 == shard]
    results = []
    for name, root in selected:
        result = await MODULE.probe_site(name, root)
        result["phase"] = "unknown20_learned"
        result["learning_transfer"] = {
            "global_transfer_path_count": len(transfer["global_transfer_paths"]),
            "learned_directory_count": len(transfer["learned_directories"]),
        }
        results.append(result)
        print(json.dumps({
            "site": name,
            "family": result.get("family"),
            "family_confidence": result.get("family_confidence"),
            "native_verified": bool((result.get("native_feed") or {}).get("verified")),
            "feed_transport": result.get("feed_transport"),
            "candidate_count": result.get("candidate_count"),
            "elapsed_s": result.get("elapsed_s"),
        }), flush=True)
    out = ROOT / "out" / "woocommerce-unknown20-learned-feed-guess"
    out.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema": "woocommerce-unknown20-learned-feed-guess/v1",
        "shard": shard,
        "shards": shards,
        "targets": [n for n, _ in selected],
        "calibration_schema": calibration.get("schema"),
        "learning_transfer": transfer,
        "results": results,
    }
    (out / f"shard-{shard}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )

if __name__ == "__main__":
    asyncio.run(main())
