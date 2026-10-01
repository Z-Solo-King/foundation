"""WooCommerce V175 public transport and advisory primitives."""
from __future__ import annotations

try:
    from tools.woocommerce_v175_contracts import *
    from tools.woocommerce_v175_discovery import *
except ModuleNotFoundError:
    from woocommerce_v175_contracts import *
    from woocommerce_v175_discovery import *

async def http_get(client: httpx.AsyncClient, url: str, cookies: Dict[str, str], timeout: float = 25.0):
    try:
        r = await client.get(url, cookies=cookies, follow_redirects=True, timeout=timeout)
        body = await r.aread()
        return r.status_code, str(r.url), r.headers, body
    except Exception as e:
        return 0, url, {}, str(e).encode()


async def http_options(client: httpx.AsyncClient, url: str, cookies: Dict[str, str], timeout: float = 15.0):
    try:
        r = await client.options(url, cookies=cookies, follow_redirects=True, timeout=timeout)
        await r.aread()
        return r.status_code, str(r.url), r.headers
    except Exception:
        return 0, url, {}


async def api_surface(root: str, user_agent: str = "") -> Tuple[List[ApiEvidence], List[str], List[str]]:
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WooCommerceV175PluginRecovery/2026.09)",
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    }
    api_out: List[ApiEvidence] = []
    blobs: List[str] = []
    ns: List[str] = []
    async with httpx.AsyncClient(headers=headers) as client:
        for path in API_PATHS:
            url = urljoin(root + "/", path)
            st, final, hdrs, body = await http_get(client, url, {}, 20)
            txt = body.decode("utf-8", "ignore")[:500_000]
            if st == 200 and path.rstrip("/") in ("/wp-json", "/wp-json/"):
                blobs.append(txt)
                ns.extend(parse_namespaces(txt))
            api_out.append(ApiEvidence(
                url=url, status=st,
                allow=hdrs.get("allow", ""),
                content_type=hdrs.get("content-type", ""),
                namespaces=parse_namespaces(txt) if "wp-json" in path and st == 200 else [],
                plugin_hits=[],
                body_read=(path == "/wp-json/" and st == 200),
                error="" if st else txt[:180],
            ))
        for path in WC_REST_PATHS:
            url = urljoin(root + "/", path)
            st, final, hdrs = await http_options(client, url, {}, 12)
            api_out.append(ApiEvidence(
                url=url, status=st, allow=hdrs.get("allow", ""),
                content_type=hdrs.get("content-type", ""), body_read=False
            ))
    return api_out, blobs, sorted(set(ns))


def discover_internal_page_urls(text: str, root: str, limit: int = 2) -> List[str]:
    """Select a tiny same-host set of store/product/category pages for deeper public discovery."""
    scored: Dict[str, int] = {}
    for raw in re.findall(r'''(?:href|data-href|data-url)=["']([^"']+)["']''', text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
            parts = urlsplit(u)
        except Exception:
            continue
        if parts.scheme not in {"http", "https"} or not same_host(u, root) or parts.fragment:
            continue
        path = (parts.path or "/").lower()
        if any(x in path for x in ("/wp-admin", "/wp-login", "/cart", "/checkout", "/my-account", "/logout")):
            continue
        score = 0
        if "/product/" in path:
            score += 100
        if any(x in path for x in ("/shop", "/store", "/products", "/product-category", "/category/")):
            score += 70
        if "post_type=product" in (parts.query or "").lower():
            score += 80
        if path in {"/", ""}:
            score -= 50
        score -= min(len(path), 40) // 10
        scored[u.split("#", 1)[0]] = max(score, scored.get(u.split("#", 1)[0], -999))
    return sorted(scored, key=lambda u: (-scored[u], len(u), u))[:max(0, limit)]


async def browser_engine(root: str, engine: str):
    try:
        from playwright.async_api import async_playwright
    except Exception as e:
        return BrowserEvidence(engine=engine, error=f"playwright_not_installed:{e}"), {}, "", []
    try:
        async with async_playwright() as p:
            launcher = getattr(p, engine)
            browser = await launcher.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="en-IN",
                extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
            )
            page = await context.new_page()
            requests_seen: List[str] = []
            response_blobs: List[str] = []
            async def on_request(req):
                try:
                    if same_host(req.url, root):
                        requests_seen.append(req.url)
                except Exception:
                    pass

            async def on_response(resp):
                try:
                    u = resp.url
                    if not same_host(u, root):
                        return
                    hdrs = await resp.all_headers()
                    ct = hdrs.get("content-type", "")
                    interesting = (
                        "json" in ct.lower() or "xml" in ct.lower() or
                        any(x in u.lower() for x in (
                            "wp-json", "admin-ajax.php", "wc-ajax", "product", "catalog", "search", "feed",
                            "google", "merchant", "ctx", "wpfm", "webtoffee", "adtribes", "woo-feed", "feedcraft", 
                            "sitemap", "robots.txt", "/api/",
                        ))
                    )
                    if not interesting:
                        return
                    requests_seen.append(u)
                    if len(response_blobs) >= 40:
                        return
                    if any(x in u.lower() for x in ("feed", "google", "merchant", "woo_feed", "woocommerce_gpf", "wpfm", "webtoffee", "adtribes", "feedcraft", "admin-ajax.php")) or "json" in ct.lower() or "xml" in ct.lower():
                        try:
                            b = await resp.body()
                            if 0 < len(b) <= 350_000:
                                response_blobs.append(b.decode("utf-8", "ignore"))
                        except Exception:
                            pass
                except Exception:
                    pass

            page.on("request", on_request)
            page.on("response", on_response)
            try:
                resp = await page.goto(root, wait_until="domcontentloaded", timeout=45_000)
                await page.wait_for_timeout(2500)
            except Exception:
                resp = None
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 3)")
                await page.wait_for_timeout(1200)
            except Exception:
                pass
            html = await page.content()
            visited_internal_urls: List[str] = []
            page_htmls = [html]
            status = getattr(resp, "status", 0) if resp else 0
            challenge = is_challenge(status, html)
            if status == 200 and not challenge and MAX_INTERNAL_PAGES:
                for internal_url in discover_internal_page_urls(html, root, MAX_INTERNAL_PAGES):
                    try:
                        internal_resp = await page.goto(internal_url, wait_until="domcontentloaded", timeout=25_000)
                        await page.wait_for_timeout(1000)
                        internal_html = await page.content()
                        visited_internal_urls.append(internal_url)
                        page_htmls.append(internal_html)
                        if is_challenge(getattr(internal_resp, "status", 0) if internal_resp else 0, internal_html):
                            challenge = True
                            break
                    except Exception:
                        continue
            html = "\\n".join(page_htmls)
            try:
                perf_urls = await page.evaluate("performance.getEntriesByType('resource').map(e => e.name)")
                if isinstance(perf_urls, list):
                    requests_seen.extend(str(x) for x in perf_urls if same_host(str(x), root))
            except Exception:
                perf_urls = []
            cookies = await context.cookies()
            cookie_names = sorted({str(c.get("name")) for c in cookies if c.get("name")})
            cookie_values = {str(c["name"]): str(c.get("value") or "") for c in cookies if c.get("name")}
            ua = ""
            try:
                ua = await page.evaluate("navigator.userAgent")
            except Exception:
                pass
            await browser.close()
            combined = html + "\n" + "\n".join(requests_seen) + "\n" + "\n".join(response_blobs)
            slugs = parse_plugin_slugs(combined)
            namespaces = parse_namespaces(combined)
            return BrowserEvidence(
                engine=engine,
                status=status,
                challenge=challenge,
                challenge_encountered=challenge,
                cf_clearance=("cf_clearance" in cookie_values or "__cf_bm" in cookie_values),
                cookie_names=cookie_names,
                user_agent=ua,
                html_len=len(html),
                visited_internal_urls=visited_internal_urls,
                plugin_asset_slugs=slugs,
                namespaces=namespaces,
                xhr_urls=sorted(set(requests_seen))[:300],
                resource_urls=sorted(set(str(x) for x in perf_urls if same_host(str(x), root)))[:300] if isinstance(perf_urls, list) else [],
                error="",
            ), {}, html, response_blobs
    except Exception as e:
        return BrowserEvidence(engine=engine, error=str(e)), {}, "", []


async def optional_cf_content(root: str) -> Tuple[Optional[str], Dict[str, Any]]:
    if not CF_BROWSER_RUN_ENABLED:
        return None, {"enabled": False, "reason": "disabled_by_default_or_scope"}
    account = os.getenv("CF_ACCOUNT_ID", "").strip()
    token = os.getenv("CF_API_TOKEN", "").strip()
    if not account or not token:
        return None, {"enabled": False, "reason": "missing_env"}
    endpoint = f"https://api.cloudflare.com/client/v4/accounts/{account}/browser-rendering/content"
    try:
        async with httpx.AsyncClient(timeout=55) as client:
            r = await client.post(
                endpoint,
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"url": root, "gotoOptions": {"waitUntil": "domcontentloaded", "timeout": 30000}, "actionTimeout": 45000},
            )
            data = r.json()
            if r.status_code != 200 or not data.get("success"):
                return None, {"enabled": True, "status": r.status_code, "error": str(data)[:300]}
            result = data.get("result")
            if isinstance(result, str):
                return result, {"enabled": True, "status": 200}
            if isinstance(result, dict):
                return str(result.get("content") or result.get("html") or ""), {"enabled": True, "status": 200}
            return "", {"enabled": True, "status": 200}
    except Exception as e:
        return None, {"enabled": True, "status": 0, "error": str(e)[:300]}


async def optional_browserless(root: str) -> Tuple[Optional[str], Dict[str, Any]]:
    enabled = os.getenv("BROWSERLESS_DIAGNOSTIC_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
    endpoint = os.getenv("BROWSERLESS_CONTENT_URL", "").strip()
    if not enabled:
        return None, {"enabled": False, "reason": "disabled_by_default_or_scope"}
    if not endpoint:
        return None, {"enabled": False, "reason": "missing_env"}
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post(endpoint, json={"url": root, "waitUntil": "domcontentloaded", "timeout": 45000})
            if r.status_code != 200:
                return None, {"enabled": True, "status": r.status_code, "error": r.text[:300]}
            return r.text, {"enabled": True, "status": 200}
    except Exception as e:
        return None, {"enabled": True, "status": 0, "error": str(e)[:300]}


async def direct_feed_probe(root: str, candidates: List[str], user_agent: str = "") -> Dict[str, Any]:
    tried = []
    seen = set()
    prioritized = []
    for candidate in candidates:
        u = urljoin(root + "/", candidate)
        if not same_host(u, root) or u in seen:
            continue
        seen.add(u)
        score = 0
        low = u.lower()
        if "woocommerce_gpf" in low or "woo_feed=" in low:
            score += 40
        if any(x in low for x in ("google", "merchant", "shopping")):
            score += 20
        if low.endswith(".xml") or ".xml?" in low:
            score += 10
        prioritized.append((score, u))
    prioritized = [u for _, u in sorted(prioritized, reverse=True)][:MAX_DIRECT_FEED_PROBES]
    headers = {
        "User-Agent": user_agent or "Mozilla/5.0 (compatible; WooCommerceV175FeedProbe/2026.09)",
        "Accept": "application/xml, application/rss+xml, text/xml, */*",
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=30) as client:
        for u in prioritized:
            try:
                r = await client.get(u)
                body = await r.aread()
                ok, count, sha = native_google_valid(body, r.headers.get("content-type", ""))
                tried.append({"url": u, "status": r.status_code, "final_url": str(r.url), "ct": r.headers.get("content-type", ""), "bytes": len(body), "native": ok})
                if ok and same_host(str(r.url), root):
                    return {"verified": True, "url": str(r.url), "item_count": count, "sha256": sha, "tried": tried[-30:]}
            except Exception as e:
                tried.append({"url": u, "status": 0, "error": str(e)[:180], "native": False})
    return {"verified": False, "url": None, "item_count": 0, "sha256": "", "tried": tried[-60:]}


async def ai_advisory(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Public-safe stub; provider advisory execution is private Operations only."""
    return {
        "enabled": False,
        "provider": None,
        "model": None,
        "status": None,
        "latency_ms": None,
        "result": {},
        "outcomes": [],
        "reason": "provider_advisory_private_operations_only",
    }

# Backward-compatible name for existing callers/tests.
groq_advisory = ai_advisory


async def passive_public_discovery(root: str) -> Dict[str, Any]:
    if not PASSIVE_INDEX_ENABLED:
        return {"enabled": False, "urls": [], "historical": [], "errors": []}
    headers = {"User-Agent": "Mozilla/5.0 (compatible; WooCommerceV175PassiveDiscovery/2026.09)", "Accept": "text/plain, application/xml, */*"}
    urls = set()
    historical = set()
    blobs = []
    errors = []
    probes = [
        "/robots.txt", "/wp-sitemap.xml", "/wp-sitemap.xml.gz", "/sitemap.xml", "/sitemap_index.xml",
        "/product-sitemap.xml", "/product-sitemap1.xml",
    ]
    directory_urls = set()
    directory_reports = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=15) as client:
        for path in probes:
            u = urljoin(root + "/", path)
            try:
                r = await client.get(u)
                body = await r.aread()
                if r.status_code == 200:
                    txt = body.decode("utf-8", "ignore")[:600_000]
                    blobs.append(txt)
                    urls.update(discover_urls_from_xml_or_text(txt, root))
                    urls.update(passive_sitemap_candidates(txt, root))
            except Exception as e:
                errors.append({"url": u, "error": str(e)[:180]})

        # Public directory indexes are an important recovery path for plugins whose feed
        # filename is generated/randomized (e.g. CTX Feed and Product Feed PRO).
        async def inspect_directory(directory: str):
            u = urljoin(root + "/", directory.lstrip("/"))
            try:
                r = await client.get(u, timeout=8)
                body = await r.aread()
                text = body.decode("utf-8", "ignore")[:250_000]
                candidates = public_directory_feed_candidates(text, root, directory) if r.status_code == 200 else []
                return {
                    "directory": directory,
                    "status": r.status_code,
                    "candidate_urls": candidates,
                }
            except Exception as e:
                return {"directory": directory, "status": 0, "candidate_urls": [], "error": str(e)[:180]}

        directory_results = await asyncio.gather(*(inspect_directory(d) for d in PLUGIN_FEED_DIRECTORIES))
        for report in directory_results:
            directory_reports.append(report)
            directory_urls.update(report.get("candidate_urls") or [])
            urls.update(report.get("candidate_urls") or [])
        if WAYBACK_ENABLED:
            try:
                pattern = quote(bare_host(root) + "/*", safe="")
                filter_expr = quote(".*(feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed).*", safe="")
                api = f"https://web.archive.org/cdx/search/cdx?url={pattern}&output=json&fl=original,statuscode,mimetype&filter=statuscode:200&filter=urlkey:{filter_expr}&collapse=urlkey&limit=80"
                r = await client.get(api, timeout=20)
                if r.status_code == 200:
                    data = r.json()
                    rows = data[1:] if isinstance(data, list) and data and isinstance(data[0], list) else data
                    for row in rows or []:
                        if isinstance(row, list) and row:
                            u = str(row[0])
                            if same_host(u, root):
                                historical.add(u)
            except Exception as e:
                errors.append({"source": "wayback", "error": str(e)[:180]})
        if COMMONCRAWL_ENABLED:
            try:
                idx = await client.get("https://index.commoncrawl.org/collinfo.json", timeout=20)
                if idx.status_code == 200:
                    coll = idx.json()
                    index_id = str(coll[0].get("id")) if coll else ""
                    if index_id:
                        pattern = quote(bare_host(root) + "/*", safe="")
                        api = f"https://index.commoncrawl.org/{index_id}-index?url={pattern}&output=json&matchType=prefix&filter=status:200&filter=url:feed|google|merchant|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed&limit=80"
                        cr = await client.get(api, timeout=25)
                        if cr.status_code == 200:
                            for line in cr.text.splitlines():
                                try:
                                    row = json.loads(line)
                                    u = str(row.get("url", ""))
                                    if same_host(u, root):
                                        historical.add(u)
                                except Exception:
                                    continue
            except Exception as e:
                errors.append({"source": "commoncrawl", "error": str(e)[:180]})
    return {
        "enabled": True,
        "urls": sorted(urls)[:300],
        "historical": sorted(historical)[:300],
        "blobs": blobs[:20],
        "errors": errors,
        "directory_candidates": sorted(directory_urls)[:240],
        "directory_reports": directory_reports[:20],
    }
