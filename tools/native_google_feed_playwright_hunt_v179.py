#!/usr/bin/env python3
import asyncio, json, os, re, sys
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

SITES=json.loads(os.environ.get("SITES_JSON","[]"))

CANDIDATE_PATTERNS=[
"/?woocommerce_gpf=google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
"/woocommerce_gpf/google","/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
"/google.xml","/google_feed.xml","/google-feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml",
"/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml",
"/gpf.xml","/product-feed.xml","/products-feed.xml","/feed/google.xml","/feed/google-products.xml","/feed/google-product-feed.xml",
"/feed/google-shopping.xml","/feed/google-shopping-feed.xml","/feed/merchant.xml","/feed/merchant-feed.xml",
"/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml",
"/catalog/feed.xml","/catalog/google.xml",
"/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml","/wp-content/uploads/google_product_feed.xml",
"/wp-content/uploads/codesolz-feeds/google.xml","/wp-content/uploads/codesolz-feeds/google-products.xml",
"/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/woo-feed/google/xml/google.xml",
"/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
"/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
"/wp-content/uploads/wppfm-feeds/google.xml",
"/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/google.xml",
"/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml","/wp-json/woo-feed/v1/google.xml",
"/wp-json/ctxfeed/v8/feeds","/wp-json/ctxfeed/v7/feeds","/wp-json/ctxfeed/v6/feeds","/wp-json/ctxfeed/v5/feeds",
"/wp-json/ctxfeed/v4/feeds","/wp-json/ctxfeed/v3/feeds","/wp-json/ctxfeed/v2/feeds","/wp-json/ctxfeed/v1/feeds",
]

FEED_WORDS=re.compile(r"(?:google|merchant|shopping|product[-_ ]?feed|woocommerce_gpf|woo[-_ ]?feed|wppfm|ctxfeed)",re.I)
CHALLENGE=re.compile(r"just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human",re.I)

def same_host(a,b):
    try:
        ha=urlparse(a).hostname.lower().lstrip("www.")
        hb=urlparse(b).hostname.lower().lstrip("www.")
        return ha==hb
    except Exception:
        return False

def absu(root,x):
    try:
        u=urljoin(root,x)
        return u if same_host(u,root) else None
    except Exception:
        return None

def native_xml(text):
    try:
        import xml.etree.ElementTree as ET
        root_el=ET.fromstring(text or "")
        root_name=root_el.tag.rsplit("}",1)[-1].lower() if isinstance(root_el.tag,str) else ""
        if root_name not in {"rss","feed"}:
            return False
        google_ns="http://base.google.com/ns/1.0"
        for item in root_el.iter():
            local=item.tag.rsplit("}",1)[-1].lower() if isinstance(item.tag,str) else ""
            if local not in {"item","entry"}:
                continue
            fields={}
            for child in list(item):
                if not isinstance(child.tag,str):
                    continue
                if child.tag.startswith("{"+google_ns+"}"):
                    fields[child.tag.rsplit("}",1)[-1].lower()]=("".join(child.itertext()) or "").strip()
            if all(fields.get(k) for k in ("id","title","link","price")):
                return True
        return False
    except Exception:
        return False

def extract_urls(text,root):
    out=set()
    s=text or ""
    for x in re.findall(r"https?://[^\s\"'<>]+",s,re.I):
        x=re.sub(r"[\),.;]+$","",x)
        if same_host(x,root) and (re.search(r"\.xml(?:\.gz)?(?:$|[?#])",x,re.I) or FEED_WORDS.search(x)): out.add(x)
    for x in re.findall(r'(?:href|loc|url|feedUrl|feed_url|fileUrl|file_url|exportUrl|export_url)\s*[:=]\s*[\'"]([^\'"]+)',s,re.I):
        u=absu(root,x)
        if u and (re.search(r"\.xml(?:\.gz)?(?:$|[?#])",u,re.I) or FEED_WORDS.search(u)): out.add(u)
    return out

async def feed_probe(page, urls):
    code=r"""
    async (urls)=>{
      const out=[];
      for(const u of urls){
        try{
          const ctl=new AbortController(), tm=setTimeout(()=>ctl.abort(),8000);
          const r=await fetch(u,{credentials:"include",redirect:"follow",signal:ctl.signal,headers:{accept:"application/xml,application/rss+xml,text/xml,text/plain,*/*"}});
          const t=await r.text(); clearTimeout(tm);
          out.push({url:u,status:r.status,final:r.url,ct:r.headers.get("content-type")||"",len:t.length,body:t.slice(0,700000)});
        }catch(e){out.push({url:u,status:0,error:String(e?.name||e)})}
      }
      return out;
    }
    """
    return await page.evaluate(code, urls)

async def one(site):
    root=site["url"].rstrip("/")
    cands={absu(root,x) for x in CANDIDATE_PATTERNS}
    cands.discard(None)
    discovery=[]; route_candidates=set(); resource_candidates=set()
    cookie_names=[]; page_info={}

    async with async_playwright() as p:
        browser=await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled","--no-sandbox","--disable-dev-shm-usage"]
        )
        context=await browser.new_context(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
            viewport={"width":1440,"height":900},
            locale="en-IN",
            java_script_enabled=True,
        )
        page=await context.new_page()
        resource_urls=set()
        def on_response(resp):
            try:
                u=resp.url
                if same_host(u,root) and (FEED_WORDS.search(u) or re.search(r"\.xml(?:\.gz)?(?:$|[?#])",u,re.I)):
                    resource_urls.add(u)
            except Exception:
                pass
        page.on("response",on_response)

        try:
            r=await page.goto(root,wait_until="domcontentloaded",timeout=30000)
        except Exception:
            r=None
        try:
            await page.wait_for_timeout(5000)
        except Exception: pass
        try:
            page_info=await page.evaluate("""()=>({href:location.href,title:document.title||"",readyState:document.readyState,bodyLen:(document.body?.innerText||"").length,htmlLen:document.documentElement?.outerHTML?.length||0,challenge:/just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(document.documentElement?.outerHTML||"")})""")
        except Exception: page_info={}
        try:
            for c in await context.cookies():
                cookie_names.append(c.get("name",""))
        except Exception: pass

        # Public discovery pages inside the same browser context.
        for path in ["/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/wp-json/"]:
            u=root+path
            try:
                rr=await page.request.get(u,timeout=15000,headers={"Accept":"application/xml,application/json,text/plain,text/html;q=.7,*/*;q=.2"})
                body=await rr.text()
                discovery.append({"url":u,"status":rr.status,"ct":rr.headers.get("content-type",""),"len":len(body)})
                for x in extract_urls(body,root): cands.add(x)
                if path=="/wp-json/":
                    # Inspect only route names and explicit URL-like values; do not persist catalog rows.
                    for m in re.finditer(r'"(/[^"]*(?:feed|google|merchant|shopping|product[^"]*)[^"]*)"\s*:',body,re.I):
                        ru=absu(root,"/wp-json"+m.group(1))
                        if ru and len(route_candidates)<80: route_candidates.add(ru)
            except Exception as e:
                discovery.append({"url":u,"status":0,"error":str(e)[:180]})

        for u in route_candidates:
            try:
                rr=await page.request.get(u,timeout=12000,headers={"Accept":"application/json,application/xml,text/plain,*/*"})
                body=await rr.text()
                for x in extract_urls(body,root): cands.add(x)
                if FEED_WORDS.search(body):
                    for x in extract_urls(body,root): resource_candidates.add(x)
            except Exception: pass

        cands.update(resource_urls)

        allc=list(cands)[:180]
        results=[]
        for i in range(0,len(allc),10):
            rows=await feed_probe(page,allc[i:i+10])
            for row in rows:
                ok=(row.get("status")==200 and same_host(row.get("final",""),root) and native_xml(row.get("body","")))
                row2={k:v for k,v in row.items() if k!="body"}
                row2["native"]=ok
                results.append(row2)
                if ok:
                    await browser.close()
                    return {"site":site["name"],"url":row["final"],"method":"playwright_same_session","tested":len(results),"candidates":len(allc),"cookie_names":sorted(set(cookie_names)),"has_cf_clearance":"cf_clearance" in cookie_names,"page":page_info,"discovery":discovery,"route_candidates":len(route_candidates),"resource_candidates":len(resource_candidates)}
        # As a final same-session pass, inspect any URL-looking strings from the rendered DOM.
        try:
            html=await page.content()
            for x in extract_urls(html,root): cands.add(x)
        except Exception: pass
        for u in [x for x in cands if x not in {r["url"] for r in results}][:60]:
            rows=await feed_probe(page,[u])
            for row in rows:
                ok=(row.get("status")==200 and same_host(row.get("final",""),root) and native_xml(row.get("body","")))
                if ok:
                    await browser.close()
                    return {"site":site["name"],"url":row["final"],"method":"playwright_rendered_dom","tested":len(results)+1,"candidates":len(cands),"cookie_names":sorted(set(cookie_names)),"has_cf_clearance":"cf_clearance" in cookie_names,"page":page_info,"discovery":discovery,"route_candidates":len(route_candidates),"resource_candidates":len(resource_candidates)}
        await browser.close()
    return {"site":site["name"],"url":None,"method":None,"tested":len(results),"candidates":len(cands),"cookie_names":sorted(set(cookie_names)),"has_cf_clearance":"cf_clearance" in cookie_names,"page":page_info,"discovery":discovery,"route_candidates":len(route_candidates),"resource_candidates":len(resource_candidates),"statuses":results[-20:]}

async def main():
    out=[]
    sem=asyncio.Semaphore(4)
    async def run(s):
        async with sem:
            try:return await one(s)
            except Exception as e:return {"site":s["name"],"url":None,"method":None,"error":str(e)}
    out=await asyncio.gather(*(run(s) for s in SITES))
    print(json.dumps({"native_google_xml_only":True,"browser":"playwright_same_context","results":out},indent=2))
if __name__=="__main__":
    asyncio.run(main())
