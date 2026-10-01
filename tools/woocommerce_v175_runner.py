"""WooCommerce V175 site runner."""
from __future__ import annotations

try:
    from tools.woocommerce_v175_contracts import *
    from tools.woocommerce_v175_discovery import *
    from tools.woocommerce_v175_transport import *
except ModuleNotFoundError:
    from woocommerce_v175_contracts import *
    from woocommerce_v175_discovery import *
    from woocommerce_v175_transport import *

async def probe_site(name: str, root: str) -> Dict[str, Any]:
    start_time = time.time()
    host = bare_host(root)
    if host in KNOWN_10:
        raise RuntimeError(f"known-site exclusion violated for target: {host}")

    source_blobs: List[str] = []
    all_requests: List[str] = []
    all_slugs: List[str] = []
    all_namespaces: List[str] = []
    browser_results: List[Dict[str, Any]] = []

    # Clean standard browser passes only. Browser state is never carried between engines.
    for engine in ("chromium", "firefox", "webkit"):
        be, _, html, response_blobs = await browser_engine(root, engine)
        browser_results.append(asdict(be))
        if not be.challenge:
            source_blobs.append(html)
            source_blobs.extend(response_blobs)
        all_requests.extend(be.xhr_urls)
        all_requests.extend(be.resource_urls)
        # Plugin slugs remain diagnostic even when a challenge is present; they never make a blocked site admissible.
        all_slugs.extend(be.plugin_asset_slugs)
        all_namespaces.extend(be.namespaces)

    challenge_encountered = any(bool(b.get("challenge_encountered")) for b in browser_results)
    clean_browser_success = any(int(b.get("status") or 0) == 200 and not b.get("challenge") for b in browser_results)

    cf_html, cf_meta = await optional_cf_content(root)
    bl_html, bl_meta = await optional_browserless(root)
    if cf_html:
        all_slugs.extend(parse_plugin_slugs(cf_html))
        all_namespaces.extend(parse_namespaces(cf_html))
    if bl_html:
        all_slugs.extend(parse_plugin_slugs(bl_html))
        all_namespaces.extend(parse_namespaces(bl_html))

    # Direct public fetch is deliberately cookie-free.
    direct_home = ""
    direct_ua = "Mozilla/5.0 (compatible; WooCommerceV175PluginRecovery/2026.09)"
    try:
        headers = {"User-Agent": direct_ua, "Accept": "text/html,application/xhtml+xml,*/*;q=.8"}
        async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=20) as client:
            r = await client.get(root)
            body = await r.aread()
            direct_home = body.decode("utf-8", "ignore")[:2_000_000]
            if r.status_code == 200 and not is_challenge(r.status_code, direct_home):
                source_blobs.append(direct_home)
            if is_challenge(r.status_code, direct_home):
                challenge_encountered = True
    except Exception:
        pass

    # Public API surface without browser cookies / clearance state.
    api_evidence: List[ApiEvidence] = []
    try:
        api_evidence, api_blobs, api_ns = await api_surface(root, direct_ua)
        source_blobs.extend(api_blobs)
        all_namespaces.extend(api_ns)
    except Exception:
        pass

    passive = await passive_public_discovery(root)
    source_blobs.extend(passive.get("blobs") or [])
    all_requests.extend(passive.get("urls") or [])
    historical = passive.get("historical") or []

    all_slugs = sorted(set(all_slugs))
    all_namespaces = sorted(set(all_namespaces))
    all_requests = sorted(set(x for x in all_requests if same_host(x, root)))[:500]
    hits = find_plugin_hits(source_blobs + all_requests, all_slugs, all_namespaces)
    family = "unknown_woocommerce"
    family_confidence = "low"
    if hits:
        family = sorted(hits, key=lambda k: (-len(hits[k]), k))[0]
        family_confidence = plugin_family_confidence(hits, all_slugs, all_namespaces)

    explicit = explicit_xml_candidates("\n".join(source_blobs + all_requests), root)
    explicit_feed_candidates = filter_explicit_feed_candidates(explicit)
    query_candidates = query_feed_candidates("\n".join(source_blobs + all_requests), root)
    candidates = list(dict.fromkeys(
        explicit_feed_candidates
        + query_candidates
        + passive.get("urls", [])
        + passive.get("directory_candidates", [])
        + historical
    ))
    candidates.extend(GENERIC_FEED_PATHS)
    if family in PLUGIN_CANDIDATES:
        candidates = PLUGIN_CANDIDATES[family] + candidates
    candidates = list(dict.fromkeys(candidates))

    api_integrated_google = family == "google_for_woocommerce" and not explicit_feed_candidates and not query_candidates
    if api_integrated_google:
        feed = {
            "verified": False,
            "url": None,
            "item_count": 0,
            "sha256": "",
            "skipped": True,
            "skip_reason": "google_for_woocommerce_is_api_integrated; no standalone_xml_feed_expected_without_public_feed_url",
            "tried": [],
        }
    else:
        # A browser challenge on the homepage does not by itself invalidate an independently
        # public feed endpoint. Feed probing remains cookie-free, and only the current feed
        # payload itself can earn native-feed verification.
        feed = await direct_feed_probe(root, candidates, direct_ua)

    admissible = native_verification_admissible(
        challenge_encountered=challenge_encountered,
        clean_browser_success=clean_browser_success,
        native_feed_verified=bool(feed.get("verified")),
    )

    evidence = {
        "site": name,
        "url": root,
        "version": "V175-derived-plugin-harness-2026.09",
        "family": family,
        "family_confidence": family_confidence,
        "family_hits": hits,
        "plugin_asset_slugs": all_slugs,
        "namespaces": all_namespaces,
        "xhr_urls": all_requests,
        "api_evidence": [asdict(x) for x in api_evidence],
        "http_api_namespaces": sorted(set(x for a in api_evidence for x in a.namespaces)),
        "browser": browser_results,
        "challenge_encountered": challenge_encountered,
        "admissible_for_native_verification": admissible,
        "cloudflare": cf_meta,
        "browserless": bl_meta,
        "passive_discovery": {
            "enabled": passive.get("enabled"),
            "current_candidate_urls": passive.get("urls", [])[:200],
            "directory_candidates": passive.get("directory_candidates", [])[:200],
            "directory_reports": passive.get("directory_reports", [])[:20],
            "historical_candidate_urls": historical[:200],
            "errors": passive.get("errors", []),
        },
        "candidate_count": len(candidates),
        "explicit_candidates": explicit[:120],
        "explicit_feed_candidates": explicit_feed_candidates[:120],
        "query_feed_candidates": query_candidates[:120],
        "native_feed": feed,
        "feed_transport": "api_integrated" if api_integrated_google else "standalone_xml_candidate_probe",
        "elapsed_s": round(time.time() - start_time, 2),
    }
    evidence["ai_advisory"] = await ai_advisory(evidence)
    return evidence


async def main() -> int:
    shard = int(os.getenv("SHARD", "1"))
    shards = int(os.getenv("SHARDS", "6"))
    selected = [(n, u) for i, (n, u) in enumerate(TARGETS) if i % shards + 1 == shard]
    out_dir = Path("out") / "woocommerce-v175-plugin-recovery"
    out_dir.mkdir(parents=True, exist_ok=True)
    results: List[Dict[str, Any]] = []
    for name, root in selected:
        result = await probe_site(name, root)
        results.append(result)
        print(json.dumps({
            "site": result["site"],
            "family": result["family"],
            "native_verified": bool(result["native_feed"].get("verified")),
            "candidate_count": result["candidate_count"],
            "elapsed_s": result["elapsed_s"],
            "browser": [(b["engine"], b["status"], b["cf_clearance"]) for b in result["browser"]],
        }), flush=True)
    payload = {
        "schema": "woocommerce-v175-plugin-recovery/v1",
        "version": "V175-derived-plugin-harness-2026.09",
        "shard": shard,
        "shards": shards,
        "targets": [n for n, _ in selected],
        "results": results,
        "summary": {            "sites": len(results),
            "native_verified": sum(1 for x in results if x["native_feed"].get("verified")),
            "challenge_encountered": sum(1 for x in results if x.get("challenge_encountered")),            "admissible_for_native_verification": sum(1 for x in results if x.get("admissible_for_native_verification")),
            "plugin_groups": {
                k: sum(1 for x in results if x["family"] == k)
                for k in sorted(set(x["family"] for x in results))
            }
        }
    }
    (out_dir / f"shard-{shard}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

# v175-run-sync: latest workflow head dispatch
