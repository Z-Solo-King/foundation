#!/usr/bin/env python3
import asyncio, json, os, re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
SITE=os.environ["SITE_NAME"]; ROOT=os.environ["SITE_ROOT"].rstrip("/")
PATTERNS=["/?woocommerce_gpf=google","/woocommerce_gpf/google","/google.xml","/google_feed.xml","/google-feed.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml","/gpf.xml","/product-feed.xml","/products-feed.xml","/feed/google.xml","/feed/google-products.xml","/feed/google-product-feed.xml","/feed/google-shopping.xml","/feed/google-shopping-feed.xml","/feed/merchant.xml","/feed/merchant-feed.xml","/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml","/catalog/feed.xml","/catalog/google.xml","/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml","/wp-content/uploads/google_product_feed.xml","/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/wppfm-feeds/google.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml","/wp-json/woo-feed/v1/google.xml","/google.xml.gz","/google-feed.xml.gz","/product-feed.xml.gz","/wp-content/uploads/google-products.xml","/wp-content/uploads/google-product-feed.xml","/wp-content/uploads/merchant-feed.xml","/wp-content/uploads/product-feed.xml"]
CH=("just a moment","cf-chl-","cf-browser-verification","cf-mitigated","managed_challenge","attention required","checking your browser","verify you are human","cf-turnstile","captcha","challenge-platform")
def same(a,b):
 try:return (urlparse(a).hostname or "").lower().lstrip("www.")==(urlparse(b).hostname or "").lower().lstrip("www.")
 except:return False
def valid(t):
 s=(t or "")[:30000].lower()
 if not t or any(x in s for x in CH): return False
 if "http://base.google.com/ns/1.0" not in t: return False
 if not re.search(r"<(?:item|entry)\b",t,re.I): return False
 return bool(re.search(r"<(?:g:|\w+:)id\b[^>]*>\s*[^<]+",t,re.I) and re.search(r"<(?:g:|\w+:)price\b",t,re.I))
async def main():
 async with async_playwright() as pw:
  b=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
  c=await b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36",locale="en-IN")
  p=await c.new_page()
  try:
   try:
    r=await p.goto(ROOT,wait_until="domcontentloaded",timeout=15000)
    browser={"status":int(r.status) if r else 0,"final_url":str(r.url) if r else ROOT}
   except Exception as e: browser={"status":0,"final_url":ROOT,"goto_error":str(e)[:180]}
   results=[]; limited=0
   for pat in PATTERNS:
    u=urljoin(ROOT+"/",pat)
    try:
     rr=await p.request.get(u,timeout=7000,max_redirects=5,headers={"accept":"application/xml,text/xml,application/rss+xml,*/*","user-agent":"Mozilla/5.0"})
     body=await rr.text()
     lim=rr.status in (403,429) or any(x in body[:20000].lower() for x in CH)
     limited += int(lim)
     results.append({"url":str(rr.url),"status":int(rr.status),"content_type":rr.headers.get("content-type",""),"bytes":len(body),"native":bool(rr.status==200 and same(str(rr.url),ROOT) and valid(body))})
     if results[-1]["native"]: break
    except PWTimeout: limited+=1
    except Exception: pass
   hit=[x for x in results if x["native"]]
   out={"schema_version":"woocommerce-22-browser-xml-guess/v2","site":SITE,"root":ROOT,"browser":browser,"candidate_count":len(PATTERNS),"tested_count":len(results),"transport_limited":limited,"status":"NATIVE_XML_FEED_VERIFIED" if hit else ("TRANSPORT_LIMITED_NO_NATIVE_FEED" if limited else "NO_NATIVE_FEED_VERIFIED"),"hits":hit}
   od=Path(os.environ.get("OUT_DIR","out")); od.mkdir(parents=True,exist_ok=True); (od/"result.json").write_text(json.dumps(out,indent=2)+"\n")
   print(json.dumps({"site":SITE,"status":out["status"],"tested":len(results),"limited":limited,"hits":hit}))
  finally:
   await c.close(); await b.close()
asyncio.run(main())
