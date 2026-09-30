#!/usr/bin/env python3
from __future__ import annotations
import asyncio, gzip, hashlib, json, os, re, time
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit
try:
    import httpx
except ModuleNotFoundError:  # pure helper tests do not require the HTTP client
    httpx = None

TARGETS = [
("Aarna Computers","https://aarnacomputers.com"),("Ads Store","https://adsstore.in"),
("EZPZ Solutions","https://www.ezpzsolutions.in"),("GamesNComps","https://gamesncomps.com"),
("hotshiftpc","https://hotshiftpc.com"),("ithunt","https://ithunt.in"),
("KC Computers","https://kccomputers.co.in"),("KRG KART","https://krgkart.com"),
("Kryptronix Gaming","https://kryptronix.in"),("NCL Computer","https://nclcomputer.com"),
("PC Kumar Infotech","https://pckumar.in"),("PCHubShop","https://www.pchubshop.com"),
("Prime ABGB","https://www.primeabgb.com"),("SCL Gaming","https://sclgaming.in"),
("Variety Infotech","https://varietyinfotech.com"),("Viper PC","https://viperpc.in"),
("Cosmic Byte","https://www.thecosmicbyte.com"),("Meckeys","https://www.meckeys.com"),
("StacksKB","https://stackskb.com"),("Theproaudio","https://www.theproaudio.com")
]
GENERIC = [
"/?woocommerce_gpf=google","/woocommerce_gpf/google",
"/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
"/products.xml","/google.xml","/google-feed.xml","/google-shopping.xml",
"/merchant.xml","/product-feed.xml"
]
HINT = re.compile(r"(feed|google|merchant|shopping|woo[_-]?feed|woocommerce_gpf|product-feed|wpfm|webappick|adtribes|webtoffee|feedcraft|apfw-feed)",re.I)
TIMEOUT=float(os.getenv("REQUEST_TIMEOUT","12"))
MAX_XML=max(8,min(24,int(os.getenv("MAX_XML_PROBES","24"))))
CONCURRENCY=max(1,min(8,int(os.getenv("SITE_CONCURRENCY","4"))))

def bare_host(u:str)->str:
    return (urlsplit(u).hostname or "").lower().removeprefix("www.")
def same_host(a:str,b:str)->bool: return bare_host(a)==bare_host(b)

def load_json(b:bytes)->Any:
    try: return json.loads(b.decode("utf-8","ignore"))
    except Exception: return None

def valid_store_product(x:Any)->bool:
    return isinstance(x,dict) and isinstance(x.get("id"),int) and bool(str(x.get("name") or "").strip()) and str(x.get("permalink") or "").startswith(("http://","https://")) and isinstance(x.get("prices"),dict)

def native_google(body:bytes,ct:str):
    raw=body
    try:
        if raw[:2]==b"\x1f\x8b" or "gzip" in ct.lower(): raw=gzip.decompress(raw)
    except Exception: return False,0,""
    s=raw.decode("utf-8","ignore"); low=s.lower()
    if "http://base.google.com/ns/1.0" not in low and "https://base.google.com/ns/1.0" not in low: return False,0,""
    blocks=re.findall(r"<(?:item|entry)\b[^>]*>.*?</(?:item|entry)>",s,re.I|re.S)
    if not blocks or any(k in low for k in ("just a moment","turnstile","captcha","access denied")): return False,0,""
    req=[r"<g:id\b[^>]*>.*?</g:id>",r"<g:title\b[^>]*>.*?</g:title>",r"<g:link\b[^>]*>.*?</g:link>",r"<g:price\b[^>]*>.*?</g:price>"]
    if not any(all(re.search(p,b,re.I|re.S) for p in req) for b in blocks): return False,0,""
    return True,len(blocks),hashlib.sha256(raw).hexdigest()

async def get(client,url,accept):
    if httpx is None:
        raise RuntimeError("httpx is required for live extraction")
    try:
        r=await client.get(url,headers={"Accept":accept},follow_redirects=True,timeout=TIMEOUT)
        return r.status_code,str(r.url),dict(r.headers),await r.aread()
    except Exception as e:
        return 0,url,{},str(e).encode()

def feed_routes(api_url:str,data:Any,root:str)->list[str]:
    routes=data.get("routes") if isinstance(data,dict) else {}
    if not isinstance(routes,dict): return []
    out=set()
    for route in routes:
        r=str(route)
        if not HINT.search(r) or "{id}" in r or "{slug}" in r or "{key}" in r: continue
        if not r.startswith("/"): r="/"+r
        u=urljoin(api_url.rstrip("/")+"/",r.lstrip("/"))
        if same_host(u,root): out.add(u)
    return sorted(out)[:80]

async def run_one(name,root,sem):
    async with sem:
        t=time.monotonic()
        async with httpx.AsyncClient(headers={"User-Agent":"Mozilla/5.0 (compatible; WooCommerceV3FeedExtractor/2026.09)"}) as c:
            api_status,api_final,api_headers,api_body=await get(c,urljoin(root+"/","wp-json/"),"application/json")
            api_data=load_json(api_body) if api_status==200 else {}
            routes=feed_routes(api_final,api_data,root)
            store_url=urljoin(root+"/","wp-json/wc/store/v1/products?per_page=100")
            sst,sfinal,sh,body=await get(c,store_url,"application/json")
            products=load_json(body) if sst==200 else None
            valid=[x for x in products if valid_store_product(x)] if isinstance(products,list) else []
            xml=await probe_xml(c,root,routes)
            return {
              "site":name,"url":root,
              "wordpress_api":{"status":api_status,"routes_count":len(api_data.get("routes",{})) if isinstance(api_data,dict) else 0,"feed_routes":routes},
              "store_api":{"verified":bool(valid),"url":sfinal if valid else None,"status":sst,
                           "reported_total":int(sh.get("x-wp-total","0") or 0),"reported_total_pages":int(sh.get("x-wp-totalpages","0") or 0),
                           "page_size":len(valid),"sample_products":[{"id":p["id"],"name":p["name"],"slug":p.get("slug"),
                           "permalink":p["permalink"],"sku":p.get("sku"),"prices":p.get("prices",{}),
                           "images":[i.get("src") for i in p.get("images",[]) if isinstance(i,dict) and i.get("src")][:5]} for p in valid[:10]]},
              "native_feed":xml,
              "transport":"woocommerce_store_api" if valid else ("native_google_xml" if xml["verified"] else "unverified"),
              "elapsed_s":round(time.monotonic()-t,2)
            }

async def probe_xml(c,root,routes):
    pool=[]
    seen=set()
    for u in routes+GENERIC:
        x=urljoin(root+"/",u.lstrip("/"))
        if same_host(x,root) and x not in seen: seen.add(x); pool.append(x)
    score=lambda u:(100 if "woocommerce_gpf" in u.lower() else 80 if "woo_feed=" in u.lower() else 40 if HINT.search(u) else 10, -len(u),u)
    pool=sorted(pool,key=score,reverse=True)[:MAX_XML]
    tried=[]
    for u in pool:
        st,final,h,b=await get(c,u,"application/xml,text/xml,application/rss+xml,*/*")
        ok,count,sha=native_google(b,h.get("content-type",""))
        tried.append({"url":u,"status":st,"final_url":final,"ct":h.get("content-type",""),"bytes":len(b),"native":ok})
        if ok and same_host(final,root):
            return {"verified":True,"url":final,"item_count":count,"sha256":sha,"tried":tried}
    return {"verified":False,"url":None,"item_count":0,"sha256":"","tried":tried}

async def main():
    shard=int(os.getenv("SHARD","1")); shards=int(os.getenv("SHARDS","6"))
    targets=[x for i,x in enumerate(TARGETS) if i%shards+1==shard]
    sem=asyncio.Semaphore(CONCURRENCY)
    rows=await asyncio.gather(*(run_one(*x,sem) for x in targets))
    out=Path("out/woocommerce-feed-v3"); out.mkdir(parents=True,exist_ok=True)
    payload={"schema":"woocommerce-feed-extraction-v3/v1","strategy":"store-api-first-route-aware-native-xml","shard":shard,"shards":shards,"results":rows}
    (out/f"shard-{shard}.json").write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding="utf-8")
    for x in rows:
        print(json.dumps({"site":x["site"],"transport":x["transport"],"store_api":x["store_api"]["verified"],"native_feed":x["native_feed"]["verified"],"total_products":x["store_api"]["reported_total"],"feed_routes":len(x["wordpress_api"]["feed_routes"]),"elapsed_s":x["elapsed_s"]}),flush=True)

if __name__=="__main__": asyncio.run(main())
