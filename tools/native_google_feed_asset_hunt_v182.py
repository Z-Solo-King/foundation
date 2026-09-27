#!/usr/bin/env python3
import asyncio,json,os,re
from urllib.parse import urljoin,urlparse
from playwright.async_api import async_playwright

SITES=json.loads(os.environ.get("SITES_JSON","[]"))
FEED=re.compile(r"(google|merchant|shopping|product[-_ ]?feed|woocommerce_gpf|woo[-_ ]?feed|wppfm|ctxfeed)",re.I)
XML=re.compile(r"\.xml(?:\.gz)?(?:[?#]|$)",re.I)
BAD=re.compile(r"just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser|verify you are human",re.I)

def same(a,b):
    try:return urlparse(a).hostname.lower().lstrip("www.")==urlparse(b).hostname.lower().lstrip("www.")
    except:return False

def absu(root,x):
    try:
        u=urljoin(root,x)
        return u if same(u,root) else None
    except:return None

def extract(text,root,out):
    t=str(text or "")
    for x in re.findall(r'https?://[^\s"\'<>]+',t,re.I):
        x=re.sub(r"[\),.;]+$","",x)
        if same(x,root) and (XML.search(x) or FEED.search(x)): out.add(x)
    for x in re.findall(r'(?:"|\'|=)(/[^"\'<>\s]+(?:\.xml(?:\.gz)?|google|merchant|shopping|feed|ctxfeed|wppfm)[^"\'<>\s]*)',t,re.I):
        u=absu(root,x)
        if u: out.add(u)

def native(t):
    if not t or BAD.search(t): return False
    if not re.match(r"^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)",t,re.I): return False
    if "http://base.google.com/ns/1.0" not in t and "https://base.google.com/ns/1.0" not in t:return False
    return all(re.search(fr"<(?:[A-Za-z_][\\w.-]*:)?{n}\b",t,re.I) for n in ["id","title","link","price"])

async def one(site):
    root=site["url"].rstrip("/")
    out={"site":site["name"],"url":None,"method":None,"cf_clearance":False,"cookies":[],"script_assets":0,"candidates":0,"validated":0,"signals":[]}
    async with async_playwright() as p:
        b=await p.chromium.launch(headless=True,args=["--disable-blink-features=AutomationControlled","--no-sandbox"])
        ctx=await b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",viewport={"width":1440,"height":900},locale="en-IN")
        pg=await ctx.new_page()
        try: await pg.goto(root,wait_until="domcontentloaded",timeout=30000)
        except: pass
        await pg.wait_for_timeout(5000)
        try:
            ck=await ctx.cookies();out["cookies"]=sorted({c.get("name","") for c in ck if c.get("name")});out["cf_clearance"]="cf_clearance" in out["cookies"]
        except: pass
        cands=set()
        try:
            html=await pg.content();extract(html,root,cands)
            data=await pg.evaluate("""()=>({scripts:[...document.scripts].map(s=>s.src).filter(Boolean),links:[...document.querySelectorAll('link[href]')].map(a=>a.href),inline:[...document.scripts].filter(s=>!s.src).map(s=>s.textContent||'').join('\\n').slice(0,180000)})""")
            for u in data.get("links",[]):
                if same(u,root) and (XML.search(u) or FEED.search(u)): cands.add(u)
            extract(data.get("inline",""),root,cands)
            scripts=[u for u in data.get("scripts",[]) if same(u,root)][:40];out["script_assets"]=len(scripts)
            for u in scripts:
                try:
                    r=await pg.request.get(u,timeout=12000,headers={"Accept":"application/javascript,text/javascript,text/plain,*/*"})
                    body=await r.text()
                    if r.status==200:
                        for x in extract_urls(body,root) if False else []: pass
                        extract(body,root,cands)
                        if FEED.search(body):
                            out["signals"].append(u)
                except: pass
        except: pass
        allc=list(cands)[:140];out["candidates"]=len(allc)
        for u in allc:
            try:
                d=await pg.evaluate("""async u=>{const r=await fetch(u,{credentials:'include',redirect:'follow',headers:{accept:'application/xml,application/rss+xml,text/xml,*/*'}});const t=await r.text();return {status:r.status,final:r.url,ct:r.headers.get('content-type')||'',text:t.slice(0,700000)}}""",u)
                out["validated"]+=1
                if d.get("status")==200 and same(d.get("final",""),root) and native(d.get("text","")):
                    out["url"]=d["final"];out["method"]="script_asset_same_session";break
            except: pass
        await b.close()
    return out

async def main():
    sem=asyncio.Semaphore(4)
    async def run(s):
        async with sem:
            try:return await one(s)
            except Exception as e:return {"site":s["name"],"url":None,"error":str(e)}
    print(json.dumps({"native_google_xml_only":True,"source":"same_session_html_script_inline_asset_mining","results":await asyncio.gather(*(run(s) for s in SITES))},indent=2))
asyncio.run(main())