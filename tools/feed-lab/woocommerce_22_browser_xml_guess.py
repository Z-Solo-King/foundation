#!/usr/bin/env python3
import asyncio, json, os, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

SITES=[
("AULA India","https://aulaindia.com"),("Aarna Computers","https://aarnacomputers.com"),
("Ads Store","https://adsstore.in"),("Cosmic Byte","https://www.thecosmicbyte.com"),
("EZPZ Solutions","https://www.ezpzsolutions.in"),("KC Computers","https://kccomputers.co.in"),
("KRG KART","https://krgkart.com"),("Kryptronix Gaming","https://kryptronix.in"),
("Meckeys","https://www.meckeys.com"),("Moskeys","https://moskeys.com"),
("NCL Computer","https://nclcomputer.com"),("PC Kumar Infotech","https://pckumar.in"),
("PCHubShop","https://www.pchubshop.com"),("Prime ABGB","https://www.primeabgb.com"),
("SCL Gaming","https://sclgaming.in"),("StacksKB","https://stackskb.com"),
("Theproaudio","https://www.theproaudio.com"),("Variety Infotech","https://varietyinfotech.com"),
("Viper PC","https://viperpc.in"),("hotshiftpc","https://hotshiftpc.com"),
("itgadgetsonline","https://itgadgetsonline.com"),("ithunt","https://ithunt.in")]
PATTERNS=[
"/?woocommerce_gpf=google","/woocommerce_gpf/google","/google.xml","/google_feed.xml","/google-feed.xml",
"/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml",
"/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml","/gpf.xml",
"/product-feed.xml","/products-feed.xml","/feed/google.xml","/feed/google-products.xml",
"/feed/google-product-feed.xml","/feed/google-shopping.xml","/feed/google-shopping-feed.xml",
"/feed/merchant.xml","/feed/merchant-feed.xml","/feeds/google.xml","/feeds/google-products.xml",
"/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml",
"/catalog/feed.xml","/catalog/google.xml","/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml",
"/wp-content/uploads/google_product_feed.xml","/wp-content/uploads/codesolz-feeds/google-products.xml",
"/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/wppfm-feeds/google.xml",
"/wp-json/feedcraft-product-feed/v1/xml","/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml",
"/wp-json/woo-feed/v1/google.xml","/google.xml.gz","/google-feed.xml.gz","/product-feed.xml.gz",
"/wp-content/uploads/google-products.xml","/wp-content/uploads/google-product-feed.xml",
"/wp-content/uploads/merchant-feed.xml","/wp-content/uploads/product-feed.xml"]
CH=("just a moment","cf-chl-","cf-browser-verification","cf-mitigated","managed_challenge",
"attention required","checking your browser","verify you are human","cf-turnstile","captcha","challenge-platform")
def same(a,b):
 try:return (urlparse(a).hostname or "").lower().lstrip("www.")==(urlparse(b).hostname or "").lower().lstrip("www.")
 except:return False
def valid(t):
 s=(t or "")[:30000].lower()
 if not t or any(x in s for x in CH): return False
 if "http://base.google.com/ns/1.0" not in t: return False
 if not re.search(r"<(?:item|entry)\b",t,re.I): return False
 return bool(re.search(r"<(?:g:|\w+:)id\b[^>]*>\s*[^<]+",t,re.I) and re.search(r"<(?:g:|\w+:)price\b",t,re.I))
async def one(name,root,pw):
 root=root.rstrip("/")
 b=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
 c=await b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",locale="en-IN")
 p=await c.new_page()
 out={"schema_version":"woocommerce-22-browser-xml-guess/v3","site":name,"root":root,"candidates":len(PATTERNS),"tested_count":0,"transport_limited":0,"hits":[]}
 try:
  try:
   r=await p.goto(root,wait_until="domcontentloaded",timeout=12000)
   out["browser"]={"status":int(r.status) if r else 0,"final_url":str(r.url) if r else root}
  except Exception as e: out["browser"]={"status":0,"final_url":root,"goto_error":str(e)[:180]}
  async def probe(pat):
   u=urljoin(root+"/",pat)
   try:
    rr=await p.request.get(u,timeout=5000,max_redirects=5,headers={"accept":"application/xml,text/xml,application/rss+xml,*/*","user-agent":"Mozilla/5.0"})
    body=await rr.text(); lim=rr.status in (403,429) or any(x in body[:20000].lower() for x in CH)
    return {"url":str(rr.url),"status":int(rr.status),"content_type":rr.headers.get("content-type",""),"bytes":len(body),"native":bool(rr.status==200 and same(str(rr.url),root) and valid(body)),"limited":lim}
   except PWTimeout: return {"url":u,"status":0,"content_type":"","bytes":0,"native":False,"limited":True}
   except Exception: return {"url":u,"status":0,"content_type":"","bytes":0,"native":False,"limited":False}
  results=[]
  for i in range(0,len(PATTERNS),8):
   batch=await asyncio.gather(*(probe(x) for x in PATTERNS[i:i+8]))
   out["transport_limited"]+=sum(1 for x in batch if x["limited"]); results.extend(batch); out["tested_count"]=len(results)
   if any(x["native"] for x in batch): break
  out["hits"]=[x for x in results if x["native"]]
  out["status"]="NATIVE_XML_FEED_VERIFIED" if out["hits"] else ("TRANSPORT_LIMITED_NO_NATIVE_FEED" if out["transport_limited"] else "NO_NATIVE_FEED_VERIFIED")
 finally:
  await c.close(); await b.close()
 return out
async def main():
 shard=int(os.environ.get("SHARD_INDEX","1")); total=int(os.environ.get("SHARD_TOTAL","4"))
 targets=[x for i,x in enumerate(SITES) if (i%total)+1==shard]
 conc=int(os.environ.get("SITE_CONCURRENCY","2"))
 sem=asyncio.Semaphore(conc)
 async with async_playwright() as pw:
  async def run(site):
   async with sem:
    try:return await asyncio.wait_for(one(*site,pw),timeout=130)
    except Exception as e:return {"schema_version":"woocommerce-22-browser-xml-guess/v3","site":site[0],"root":site[1],"status":"RUNNER_ERROR","error":str(e)[:220]}
  results=await asyncio.gather(*(run(x) for x in targets))
 outdir=Path(os.environ.get("OUT_DIR","out/browser-xml-guess")); outdir.mkdir(parents=True,exist_ok=True)
 payload={"schema_version":"woocommerce-22-browser-xml-guess-shard/v1","shard":shard,"shard_total":total,
          "method":"same-session naming-only XML probe","policy":"No product APIs/catalog extraction; no HTML/JS/XHR feed URL mining; no CAPTCHA solving or Cloudflare challenge bypass; same-origin validation required.",
          "site_count":len(results),"results":sorted(results,key=lambda r:r["site"].lower())}
 (outdir/f"shard-{shard}.json").write_text(json.dumps(payload,indent=2)+"\n")
 print(json.dumps({"shard":shard,"site_count":len(results),"hits":sum(bool(r.get("hits")) for r in results),
                   "transport_limited":sum(r.get("transport_limited",0) for r in results)}))
if __name__=="__main__": asyncio.run(main())
