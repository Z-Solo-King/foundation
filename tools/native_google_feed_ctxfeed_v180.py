#!/usr/bin/env python3
import asyncio, json, os, re
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

SITES=json.loads(os.environ.get("SITES_JSON","[]"))
PLUGIN_ROUTES=[
  "/wp-json/ctxfeed/v8/feeds",
  "/wp-json/ctxfeed/v8/feeds?template=google",
  "/wp-json/ctxfeed/v8/feeds/templates",
  "/wp-json/ctxfeed/v8/status",
  "/wp-json/ctxfeed/v8/channels",
  "/wp-json/ctxfeed/v7/feeds",
  "/wp-json/ctxfeed/v6/feeds",
  "/wp-json/ctxfeed/v5/feeds",
  "/wp-json/ctxfeed/v4/feeds",
  "/wp-json/ctxfeed/v3/feeds",
  "/wp-json/ctxfeed/v2/feeds",
  "/wp-json/ctxfeed/v1/feeds",
]
FEED=re.compile(r"(?:google|merchant|shopping|feed|product[-_ ]?feed|woo|ctxfeed|wppfm)",re.I)

def same(a,b):
    try:
        return urlparse(a).hostname.lower().lstrip("www.") == urlparse(b).hostname.lower().lstrip("www.")
    except: return False

def extract_urls(obj,root,out):
    if isinstance(obj,dict):
        for k,v in obj.items():
            lk=str(k).lower()
            if isinstance(v,str):
                if re.match(r"^(?:https?:)?//|^/",v) and (FEED.search(lk) or re.search(r"\.xml(?:$|[?#])",v,re.I) or FEED.search(v)):
                    u=urljoin(root,v)
                    if same(u,root): out.add(u)
                if FEED.search(lk) and re.match(r"^https?://",v,re.I):
                    u=urljoin(root,v)
                    if same(u,root): out.add(u)
            else:
                extract_urls(v,root,out)
    elif isinstance(obj,list):
        for v in obj: extract_urls(v,root,out)

async def one(site):
    root=site["url"].rstrip("/")
    out={"site":site["name"],"url":None,"cookie_names":[],"cf_clearance":False,"page":{},"routes":[],"feed_urls":[],"files":[]}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled","--no-sandbox"])
        context=await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
            viewport={"width":1440,"height":900}, locale="en-IN"
        )
        page=await context.new_page()
        try: await page.goto(root,wait_until="domcontentloaded",timeout=30000)
        except: pass
        await page.wait_for_timeout(4500)
        try:
            out["page"]=await page.evaluate("""()=>({href:location.href,title:document.title||"",readyState:document.readyState,bodyLen:(document.body?.innerText||"").length,challenge:/just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(document.documentElement?.outerHTML||"")})""")
        except: pass
        try:
            cookies=await context.cookies()
            out["cookie_names"]=sorted({c.get("name","") for c in cookies if c.get("name")})
            out["cf_clearance"]="cf_clearance" in out["cookie_names"]
        except: pass

        # Inspect WordPress route index and plugin assets without collecting catalog data.
        route_index=root+"/wp-json/"
        try:
            rr=await page.request.get(route_index,timeout=15000,headers={"Accept":"application/json"})
            body=await rr.text()
            out["wp_json_status"]=rr.status
            out["wp_json_len"]=len(body)
            for m in re.finditer(r'"(/[^"]+ctxfeed[^"]*)"\s*:',body,re.I):
                out["files"].append(m.group(1)[:300])
            for m in re.finditer(r'https?://[^"\\s<>]+(?:ctxfeed|wppfm|feed)[^"\\s<>]*',body,re.I):
                u=m.group(0).rstrip('",);')
                if same(u,root): out["feed_urls"].append(u)
        except Exception as e:
            out["wp_json_status"]=0

        # Query public GET routes only; never POST or generate feeds.
        for path in PLUGIN_ROUTES:
            u=root+path
            rec={"url":u}
            try:
                rr=await page.request.get(u,timeout=12000,headers={"Accept":"application/json,application/xml,text/plain,*/*"})
                body=await rr.text()
                rec.update({"status":rr.status,"ct":rr.headers.get("content-type",""),"len":len(body)})
                if rr.status==200:
                    try:
                        j=json.loads(body)
                        rec["json_keys"]=sorted(list(j.keys()))[:80] if isinstance(j,dict) else []
                        found=set(); extract_urls(j,root,found)
                        for x in found:
                            if x not in out["feed_urls"]: out["feed_urls"].append(x)
                    except Exception:
                        for m in re.finditer(r'(?:https?://|/)[^"\'<>\s]+\.xml(?:\?[^"\'<>\s]+)?',body,re.I):
                            u2=urljoin(root,m.group(0))
                            if same(u2,root): out["feed_urls"].append(u2)
            except Exception as e:
                rec["status"]=0
                rec["error"]=str(e)[:180]
            out["routes"].append(rec)

        # Explicit URL validation in same browser context, no catalog persistence.
        candidates=[]
        seen=set()
        for u in out["feed_urls"]:
            if u not in seen: seen.add(u); candidates.append(u)
        for u in candidates[:60]:
            try:
                data=await page.evaluate("""async u=>{
                  const r=await fetch(u,{credentials:"include",redirect:"follow",headers:{accept:"application/xml,application/rss+xml,text/xml,*/*"}});
                  return {status:r.status,final:r.url,ct:r.headers.get("content-type")||"",text:(await r.text()).slice(0,700000)}
                }""",u)
                text=data.get("text","")
                # Strict native check; URL-only output.
                ok=(data.get("status")==200 and same(data.get("final",""),root)
                    and re.match(r"^\s*(?:<\?xml[^>]*>\s*)?<rss\b",text,re.I)
                    and "http://base.google.com/ns/1.0" in text
                    and re.search(r"<(?:g:)?(?:id|title|link|price)\b",text,re.I)
                    and not re.search(r"just a moment|cf-chl-|turnstile|captcha|access denied|attention required",text,re.I))
                if ok:
                    out["url"]=data["final"]; out["method"]="ctxfeed_route_same_context"
                    break
            except: pass
        out["feed_urls"]=sorted(set(out["feed_urls"]))[:80]
        await browser.close()
    return out

async def main():
    sem=asyncio.Semaphore(4)
    async def run(s):
        async with sem:
            try:return await one(s)
            except Exception as e:return {"site":s["name"],"url":None,"error":str(e)}
    print(json.dumps({"native_google_xml_only":True,"plugin_public_route_only":True,"results":await asyncio.gather(*(run(s) for s in SITES))},indent=2))
asyncio.run(main())