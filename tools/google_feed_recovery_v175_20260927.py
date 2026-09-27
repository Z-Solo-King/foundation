#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import time
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import httpx

try:
    from curl_cffi.requests import AsyncSession as CurlAsyncSession
except Exception:
    CurlAsyncSession = None

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None

try:
    from defusedxml import ElementTree as ET
except Exception:
    import xml.etree.ElementTree as ET


GOOGLE_NS = "http://base.google.com/ns/1.0"
SITE_TIMEOUT = 8 * 60
FAST_TIMEOUT = 22
LONG_TIMEOUT = 210
MAX_BODY_BYTES = 50 * 1024 * 1024  # V175 recovery ceiling; large feeds use streaming/partial paths
XHR_TIMEOUT_MS = 60000
BROWSER_TIMEOUT_MS = 50000
CONCURRENCY = 4

# OnlySDD was already verified separately and is intentionally excluded.
TARGETS = {
    "Aarna Computers": "https://aarnacomputers.com",
    "Ads Store": "https://adsstore.in",
    "avikaretails": "https://avikaretails.com",
    "EZPZ Solutions": "https://www.ezpzsolutions.in",
    "GamesNComps": "https://gamesncomps.com",
    "Geekbees": "https://geekbees.in",
    "hotshiftpc": "https://hotshiftpc.com",
    "itgadgetsonline": "https://itgadgetsonline.com",
    "ithunt": "https://ithunt.in",
    "kccomputers": "https://kccomputers.co.in",
    "KRG KART": "https://krgkart.com",
    "Kryptronix Gaming": "https://kryptronix.in",
    "NCL Computer": "https://nclcomputer.com",
    "networkitstore": "https://networkitstore.in",
    "nexusinfosys": "https://www.mynexusinfosys.com",
    "PC Kumar Infotech": "https://pckumar.in",
    "PC Studio": "https://www.pcstudio.in",
    "PCHubShop": "https://www.pchubshop.com",
    "Prime ABGB": "https://www.primeabgb.com",
    "quickincomputers": "https://quickincomputers.com",
    "SCL Gaming": "https://sclgaming.in",
    "solankienterprises": "https://solankienterprises.com",
    "Variety Infotech": "https://varietyinfotech.com",
    "Viper PC": "https://viperpc.in",
    "AULA India": "https://aulaindia.com",
    "Cosmic Byte": "https://www.thecosmicbyte.com",
    "Meckeys": "https://www.meckeys.com",
    "Moskeys": "https://moskeys.com",
    "Ninja Dog": "https://ninjadog.in",
    "Stackskb": "https://stackskb.com",
    "Theproaudio": "https://www.theproaudio.com",
}

V175_FEED_PATHS = (
    "/merchant-feed.xml", "/merchant_feed.xml",
    "/google_feed.xml", "/google-feed.xml",
    "/google_base.xml", "/googlebase.xml",
    "/google.xml", "/google-shopping.xml", "/google-shopping-feed.xml",
    "/product-feed.xml", "/products-feed.xml",
    "/feed_products.xml", "/products.xml",
    "/feeds/google.xml", "/feeds/google-products.xml",
    "/feeds/google-product-feed.xml", "/feeds/products.rss",
    "/feed.xml", "/rss.xml", "/atom.xml",
    "/products.rss", "/feed", "/rss", "/store/feed",
    "/feed/products", "/products/feed",
    "/?feed=products", "/?feed=google", "/?feed=merchant",
    "/?woocommerce_gpf=google",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
    "/?woocommerce_gpf=google&gpf_start=1&gpf_limit=250",
    "/index.php?route=extension/feed/google_base",
    "/index.php?route=feed/google_base",
    "/index.php?route=extension/feed/google_merchant",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
)

IMPERSONATIONS = ("chrome146", "chrome145", "chrome142", "chrome136", "chrome133a", "firefox147", "safari18_0")
CHALLENGE_MARKERS = (
    "just a moment", "cf-chl", "cf-browser-verification", "cf-mitigated",
    "verify you are human", "attention required", "challenge-platform",
    "cf-turnstile", "managed_challenge", "cdn-cgi/challenge",
    "enable javascript and cookies",
)
FEED_HINT_RE = re.compile(r"(google|merchant|shopping|feed|rss|xml|woocommerce_gpf|product-feed)", re.I)
XML_CT_RE = re.compile(r"(xml|rss|atom)", re.I)


def root_of(url: str) -> str:
    p = urlsplit(url)
    return f"{p.scheme}://{p.netloc}"


def same_origin(a: str, root: str) -> bool:
    try:
        return urlsplit(a).netloc.lower() == urlsplit(root).netloc.lower()
    except Exception:
        return False


def is_challenge(status: int, body: str) -> bool:
    if status in (403, 429, 451, 503, 520, 521, 522, 523, 524):
        return True
    sample = (body or "")[:10000].lower()
    return any(marker in sample for marker in CHALLENGE_MARKERS)


def looks_xml(content_type: str, body: str) -> bool:
    head = (body or "")[:12000].lower()
    return bool(XML_CT_RE.search(content_type or "") or "<rss" in head or "<feed" in head or "<item" in head or "<entry" in head)


def strict_feed_validation(body: str, content_type: str) -> dict | None:
    if not body or not looks_xml(content_type, body):
        return None
    head = body[:200000]
    if GOOGLE_NS not in head:
        return None
    if not re.search(r"<(?:item|entry)\b", body, re.I):
        return None
    return {"strict_google_merchant": True, "bytes": len(body.encode("utf-8", "ignore"))}


def parse_feed_items(body: str, source_url: str) -> list[dict]:
    if not strict_feed_validation(body, "application/xml"):
        return []
    rows = []
    try:
        for _, elem in ET.iterparse(BytesIO(body.encode("utf-8", "ignore")), events=("end",)):
            tag = str(elem.tag)
            local = tag.rsplit("}", 1)[-1].lower()
            if local not in ("item", "entry"):
                continue
            values = {}
            for child in list(elem):
                ctag = str(child.tag)
                clocal = ctag.rsplit("}", 1)[-1].lower()
                text = "".join(child.itertext()).strip()
                if text and clocal:
                    values[clocal] = text
            title = values.get("title", "").strip()
            if not title:
                elem.clear()
                continue
            link = values.get("link", "") or values.get("id", "")
            price = values.get("price", "")
            currency = values.get("currency", "")
            availability = values.get("availability", "").lower()
            stock = "In Stock" if "in_stock" in availability or availability == "in stock" else ("Out of Stock" if "out" in availability else "")
            rows.append({
                "name": title[:500],
                "url": link,
                "price": price,
                "currency": currency,
                "stock": stock,
                "sku": values.get("id") or values.get("mpn") or values.get("sku") or "",
                "brand": values.get("brand", ""),
                "image": values.get("image_link") or values.get("image") or "",
                "source_type": "merchant-feed-xhr-recovery",
                "feed_url": source_url,
            })
            elem.clear()
    except Exception:
        return []
    return rows


async def curl_get(session, url: str, *, timeout: float, headers: dict, impersonate: str, cookies: dict | None = None) -> tuple[int, str, dict, float]:
    if session is None:
        return 0, "", {}, 0.0
    merged = dict(headers)
    if cookies:
        merged["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    started = time.monotonic()
    try:
        resp = await session.get(
            url,
            headers=merged,
            timeout=timeout,
            impersonate=impersonate,
            allow_redirects=True,
        )
        raw = resp.content
        if len(raw) > MAX_BODY_BYTES:
            return 413, "", dict(resp.headers), time.monotonic() - started
        body = raw.decode("utf-8", "ignore")
        return int(resp.status_code), body, dict(resp.headers), time.monotonic() - started
    except Exception as exc:
        return 0, str(exc), {}, time.monotonic() - started


async def browser_discover(root: str) -> dict:
    result = {"ok": False, "html": "", "cookies": {}, "ua": "", "xhr": [], "requests": [], "response_bodies": [], "pages": []}
    if async_playwright is None:
        result["error"] = "playwright_unavailable"
        return result
    seen = set()
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            context = await browser.new_context(viewport={"width": 1366, "height": 768}, java_script_enabled=True)
            page = await context.new_page()

            body_tasks = []

            def on_request(request):
                try:
                    u = request.url or ""
                    if not same_origin(u, root):
                        return
                    kind = str(request.resource_type or "").lower()
                    if kind in ("xhr", "fetch") or FEED_HINT_RE.search(u):
                        result["requests"].append({"url": u, "method": request.method, "resource_type": kind})
                except Exception:
                    return

            def on_response(response):
                try:
                    u = response.url or ""
                    if not same_origin(u, root):
                        return
                    ct = (response.headers or {}).get("content-type", "")
                    kind = str(response.request.resource_type or "").lower()
                    interesting = (
                        kind in ("xhr", "fetch")
                        or FEED_HINT_RE.search(u)
                        or XML_CT_RE.search(ct)
                        or "json" in ct.lower()
                        or "/api/" in u.lower()
                        or "wp-json" in u.lower()
                        or "graphql" in u.lower()
                    )
                    if not interesting:
                        return
                    result["xhr"].append({"url": u, "status": response.status, "content_type": ct, "resource_type": kind})
                    if response.status == 200 and (FEED_HINT_RE.search(u) or XML_CT_RE.search(ct)):
                        async def capture():
                            try:
                                body = await response.text()
                                if len(body.encode("utf-8", "ignore")) <= 8 * 1024 * 1024:
                                    result["response_bodies"].append({
                                        "url": u, "status": response.status,
                                        "content_type": ct, "body": body
                                    })
                            except Exception:
                                pass
                        body_tasks.append(asyncio.create_task(capture()))
                except Exception:
                    return

            page.on("request", on_request)
            page.on("response", on_response)

            page_paths = [
                root,
                urljoin(root + "/", "shop/"),
                urljoin(root + "/", "products/"),
                urljoin(root + "/", "product-category/"),
            ]
            for target in page_paths:
                if len(result["pages"]) >= 4:
                    break
                try:
                    await page.goto(target, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT_MS)
                    await page.wait_for_timeout(3500)
                    result["pages"].append({"url": target, "final_url": page.url(), "status": 200})
                    if not result["html"]:
                        result["html"] = await page.content()
                except Exception:
                    continue

            if body_tasks:
                await asyncio.gather(*body_tasks, return_exceptions=True)
            try:
                result["ua"] = await page.evaluate("navigator.userAgent")
            except Exception:
                result["ua"] = "Mozilla/5.0"
            try:
                for c in await context.cookies():
                    if c.get("name"):
                        result["cookies"][c["name"]] = c["value"]
            except Exception:
                pass
            result["ok"] = bool(result["html"] or result["xhr"] or result["requests"])
            await browser.close()
    except Exception as exc:
        result["error"] = str(exc)
    return result


async def browser_xhr_probe(root: str, candidates: list[str], *, timeout_ms: int = XHR_TIMEOUT_MS) -> list[dict]:
    if async_playwright is None:
        return []
    out = []
    candidates = list(dict.fromkeys(candidates))[:18]
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled", "--no-sandbox"])
            context = await browser.new_context(viewport={"width": 1366, "height": 768}, java_script_enabled=True)
            page = await context.new_page()
            await page.goto(root, wait_until="domcontentloaded", timeout=BROWSER_TIMEOUT_MS)
            js = """
            async ({urls, timeout}) => {
              const one = (url) => new Promise(resolve => {
                const started = performance.now();
                const x = new XMLHttpRequest();
                let done = false;
                const finish = (v) => { if (done) return; done = true; resolve(v); };
                const timer = setTimeout(() => finish({
                  url, ok:false, error:"timeout", elapsed_ms:Math.round(performance.now()-started)
                }), timeout);
                try {
                  x.open("GET", url, true);
                  x.timeout = timeout;
                  x.setRequestHeader("Accept","application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2");
                  x.onload = () => {
                    clearTimeout(timer);
                    finish({
                      url:x.responseURL || url, ok:true, status:x.status,
                      content_type:x.getResponseHeader("content-type") || "",
                      body:x.responseText || "",
                      elapsed_ms:Math.round(performance.now()-started)
                    });
                  };
                  x.onerror = () => { clearTimeout(timer); finish({url,ok:false,error:"network"}); };
                  x.ontimeout = () => { clearTimeout(timer); finish({url,ok:false,error:"timeout"}); };
                  x.send();
                } catch (e) {
                  clearTimeout(timer);
                  finish({url,ok:false,error:String(e)});
                }
              });
              return Promise.all(urls.map(one));
            }
            """
            out = await page.evaluate(js, {"urls": candidates, "timeout": timeout_ms})
            await browser.close()
    except Exception:
        return []
    return out


def make_feed_candidates(origin: str) -> list[str]:
    paths = list(V175_FEED_PATHS)
    paths.extend([
        "/woocommerce_gpf/google",
        "/google-merchant.xml",
        "/google-merchant-feed.xml",
        "/merchant.xml",
        "/gmerchant.xml",
        "/gpf.xml",
        "/google-products.xml",
        "/google-product-feed.xml",
        "/google_feed.php",
        "/product-feed.php",
        "/feed/google",
    ])
    for limit in (25, 50, 100, 250, 500):
        for start in (0, limit, limit * 2):
            paths.append(f"/?woocommerce_gpf=google&gpf_start={start}&gpf_limit={limit}")
            paths.append(f"/woocommerce_gpf/google?gpf_start={start}&gpf_limit={limit}")
    return list(dict.fromkeys(origin + p for p in paths))


async def nodriver_warm(root: str) -> dict:
    result = {"ok": False, "html": "", "cookies": {}, "ua": ""}
    try:
        import nodriver as uc
    except Exception as exc:
        result["error"] = f"nodriver_unavailable:{exc}"
        return result
    try:
        exe = os.environ.get("NODRIVER_CHROME_PATH") or None
        browser = await uc.start(
            headless=True,
            sandbox=False,
            browser_executable_path=exe,
            browser_args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ],
        )
        page = await browser.get(root)
        await page.sleep(5)
        try:
            html = await page.get_content()
        except Exception:
            html = ""
        try:
            ua = await page.evaluate("navigator.userAgent") or ""
        except Exception:
            ua = ""
        cookies = {}
        try:
            jar = await browser.cookies.get_all()
            for cookie in jar or []:
                name = getattr(cookie, "name", None) or (
                    cookie.get("name") if isinstance(cookie, dict) else None
                )
                value = getattr(cookie, "value", None) or (
                    cookie.get("value") if isinstance(cookie, dict) else None
                )
                if name:
                    cookies[str(name)] = str(value or "")
        except Exception:
            pass
        try:
            await browser.stop()
        except Exception:
            pass
        result.update({"ok": bool(html), "html": html or "", "cookies": cookies, "ua": ua})
    except Exception as exc:
        result["error"] = str(exc)
    return result


async def site_recover(name: str, root: str, outdir: Path) -> dict:
    deadline = time.monotonic() + SITE_TIMEOUT
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "feeds").mkdir(parents=True, exist_ok=True)

    origin = root_of(root.rstrip("/"))
    candidates = make_feed_candidates(origin)
    browser = {"ok": False, "html": "", "cookies": {}, "ua": "", "xhr": [], "pages": []}
    records = []
    verified = {}

    async def record_verified(url: str, body: str, ct: str, method: str, elapsed: float):
        v = strict_feed_validation(body, ct)
        if not v:
            return
        rows = parse_feed_items(body, url)
        item_count = len(rows)
        rec = {
            "url": url,
            "method": method,
            "elapsed_s": round(elapsed, 3),
            "content_type": ct,
            "bytes": len(body.encode("utf-8", "ignore")),
            "item_count": item_count,
            "strict_google_merchant": True,
        }
        verified[url] = (rec, body)

    # Lane A: browser warm + XHR/HTML discovery.
    browser = await browser_discover(root)
    candidates.extend(x["url"] for x in browser.get("xhr", []) if x.get("url"))
    candidates.extend(x["url"] for x in browser.get("requests", []) if x.get("url"))
    for captured in browser.get("response_bodies", []):
        await record_verified(
            captured.get("url") or root,
            captured.get("body") or "",
            captured.get("content_type") or "",
            "browser-response-body",
            0.0,
        )
    html = browser.get("html") or ""
    for u in re.findall(r'https?://[^"\'<>\s]+', html):
        if same_origin(u, root) and FEED_HINT_RE.search(u):
            candidates.append(u)
    for href in re.findall(r'<link[^>]+href=["\']([^"\']+)["\']', html, re.I):
        u = urljoin(root + "/", href)
        if same_origin(u, root) and (FEED_HINT_RE.search(u) or "alternate" in href.lower()):
            candidates.append(u)

    for raw in re.findall(r'''(?:https?://[^"'<>\s]+|/[^"'<>\s]+)''', html):
        clean = raw.replace("\\/", "/")
        if "woocommerce_gpf" in clean.lower() or re.search(r'''/woocommerce_gpf/[^"'<>\s]+''', clean, re.I):
            candidates.append(urljoin(root + "/", clean))

    candidates = list(dict.fromkeys(candidates))
    strong = [u for u in candidates if FEED_HINT_RE.search(u)]
    if not strong:
        strong = candidates[:18]

    # Lane B: explicit in-page XHR replay against strong candidates.
    if time.monotonic() < deadline and strong:
        xhr_results = await browser_xhr_probe(root, strong[:36])
        for r in xhr_results:
            rec = {
                "url": r.get("url"),
                "method": "browser-XHR",
                "status": r.get("status"),
                "content_type": r.get("content_type", ""),
                "elapsed_s": round(float(r.get("elapsed_ms", 0))/1000, 3) if r.get("elapsed_ms") else None,
                "bytes": len((r.get("body") or "").encode("utf-8", "ignore")),
                "error": r.get("error"),
            }
            records.append(rec)
            if r.get("ok") and r.get("status") == 200:
                await record_verified(
                    r.get("url") or root,
                    r.get("body") or "",
                    r.get("content_type", ""),
                    "browser-XHR",
                    float(r.get("elapsed_ms", 0))/1000.0,
                )

    # Lane C: V175 nodriver browser escalation.
    if not verified and time.monotonic() < deadline:
        nd = await nodriver_warm(root)
        if nd.get("ok"):
            if nd.get("ua"):
                browser["ua"] = nd.get("ua")
            if nd.get("cookies"):
                browser["cookies"] = nd.get("cookies")
            nd_html = nd.get("html") or ""
            for raw in re.findall(r'''(?:https?://[^"'<>\s]+|/[^"'<>\s]+)''', nd_html):
                clean = raw.replace("\\/", "/")
                if FEED_HINT_RE.search(clean) or "woocommerce_gpf" in clean.lower():
                    candidates.append(urljoin(root + "/", clean))
            candidates = list(dict.fromkeys(candidates))

    # Lane C: curl_cffi impersonation ladder, with browser cookies/UA reuse after warm.
    if CurlAsyncSession is not None and time.monotonic() < deadline:
        async with CurlAsyncSession() as session:
            headers = {
                "Accept": "application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2",
                "Referer": root,
                "User-Agent": browser.get("ua") or "Mozilla/5.0",
            }

            queue = list(dict.fromkeys(str(u) for u in strong + candidates if u))
            # First pass: cheap requests, 4 at a time.
            sem = asyncio.Semaphore(CONCURRENCY)
            async def fast_probe(u):
                async with sem:
                    if time.monotonic() >= deadline:
                        return
                    for imp in IMPERSONATIONS[:4]:
                        st, body, rh, elapsed = await curl_get(
                            session, u, timeout=FAST_TIMEOUT, headers=headers,
                            impersonate=imp, cookies=browser.get("cookies") or None
                        )
                        records.append({
                            "url": u, "method": f"curl_cffi:{imp}", "status": st,
                            "content_type": rh.get("content-type", ""), "elapsed_s": round(elapsed,3),
                            "bytes": len(body.encode("utf-8","ignore")),
                            "challenge": is_challenge(st, body),
                        })
                        if st == 200:
                            await record_verified(u, body, rh.get("content-type",""), f"curl_cffi:{imp}", elapsed)
                        if st == 200 or (st not in (0, 403, 429, 503) and not is_challenge(st, body)):
                            break

            await asyncio.gather(*(fast_probe(u) for u in queue[:42]))

            # Lane D: slow/large-feed replay. Strong feed URLs only; 60s+ is allowed.
            if not verified and time.monotonic() < deadline:
                long_candidates = [u for u in queue if FEED_HINT_RE.search(u)]
                async def long_probe(u):
                    if time.monotonic() >= deadline:
                        return
                    for imp in IMPERSONATIONS[:3]:
                        st, body, rh, elapsed = await curl_get(
                            session, u, timeout=LONG_TIMEOUT, headers=headers,
                            impersonate=imp, cookies=browser.get("cookies") or None
                        )
                        records.append({
                            "url": u, "method": f"curl_cffi-long:{imp}", "status": st,
                            "content_type": rh.get("content-type",""), "elapsed_s": round(elapsed,3),
                            "bytes": len(body.encode("utf-8","ignore")),
                            "slow_lane": True, "challenge": is_challenge(st, body),
                        })
                        if st == 200:
                            await record_verified(u, body, rh.get("content-type",""), f"curl_cffi-long:{imp}", elapsed)
                            if u in verified:
                                break
                await asyncio.gather(*(long_probe(u) for u in long_candidates[:16]))

    # Save raw feed artifacts and report.
    safe = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "site"
    for i, (url, (rec, body)) in enumerate(sorted(verified.items(), key=lambda x: x[0])):
        path = outdir / "feeds" / f"{safe}-{i}.xml"
        path.write_text(body, encoding="utf-8")
        rec["artifact"] = str(path)
    report = {
        "schema_version": "v175-derived-google-feed-recovery/v1",
        "site": name,
        "root": root,
        "elapsed_s": round(SITE_TIMEOUT - max(0, deadline-time.monotonic()), 3),
        "browser_discovery": {
            "ok": browser.get("ok", False),
            "xhr_count": len(browser.get("xhr") or []),
            "pages": browser.get("pages") or [],
            "ua": browser.get("ua", ""),
        },
        "candidate_count": len(candidates),
        "verified_feed_count": len(verified),
        "verified_feeds": [v[0] for v in sorted(verified.values(), key=lambda x: x[0]["url"])],
        "records": records,
    }
    (outdir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (outdir / "candidates.json").write_text(json.dumps({
        "site": name, "root": root, "candidates": candidates,
        "browser_xhr_candidates": browser.get("xhr") or [],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-name", required=True)
    ap.add_argument("--site-url", required=True)
    ap.add_argument("--outdir", default="out/wc-google-feed-v175")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    report = await site_recover(args.site_name, args.site_url, outdir)
    print(json.dumps({
        "site": args.site_name,
        "verified_feed_count": report["verified_feed_count"],
        "verified_feeds": report["verified_feeds"],
        "candidate_count": report["candidate_count"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
