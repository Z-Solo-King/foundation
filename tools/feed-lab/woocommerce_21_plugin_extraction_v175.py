#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json, os, re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

VERSION="V175-derived-21-plugin-extraction-v1"
SITES=[
("AULA India","https://aulaindia.com"),
("Aarna Computers","https://aarnacomputers.com"),
("Ads Store","https://adsstore.in"),
("Cosmic Byte","https://www.thecosmicbyte.com"),
("EZPZ Solutions","https://www.ezpzsolutions.in"),
("KC Computers","https://kccomputers.co.in"),
("KRG KART","https://krgkart.com"),
("Kryptronix Gaming","https://kryptronix.in"),
("Meckeys","https://www.meckeys.com"),
("Moskeys","https://moskeys.com"),
("NCL Computer","https://nclcomputer.com"),
("PC Kumar Infotech","https://pckumar.in"),
("PCHubShop","https://www.pchubshop.com"),
("Prime ABGB","https://www.primeabgb.com"),
("SCL Gaming","https://sclgaming.in"),
("StacksKB","https://stackskb.com"),
("Theproaudio","https://www.theproaudio.com"),
("Variety Infotech","https://varietyinfotech.com"),
("Viper PC","https://viperpc.in"),
("hotshiftpc","https://hotshiftpc.com"),
("ithunt","https://ithunt.in"),
]
CHALLENGE_MARKERS=("just a moment","cf-chl-","cf-browser-verification","cf-mitigated","managed_challenge",
"attention required","checking your browser","enable javascript and cookies","verify you are human",
"cf-turnstile","captcha","challenge-platform")
KNOWN={
"woocommerce-google-product-feed":"woocommerce_google_product_feed",
"woo-feed":"ctx_feed_webappick",
"webappick-product-feed-for-woocommerce":"ctx_feed_webappick",
"ctx-feed":"ctx_feed_webappick",
"woo-product-feed-pro":"adtribes_product_feed_pro",
"merchant-feed-booster-lite-for-woocommerce":"codesolz_feed",
"thebasics-product-feed":"feedcraft",
"product-feed-manager":"wpfm_product_feed_manager",
"wppfm":"wpfm_product_feed_manager",
"google-listings-and-ads":"google_for_woocommerce",
}
DENY=re.compile(r"^(instagram-feed|facebook-for-woocommerce|advanced-ads|feedzy-rss-feeds)$",re.I)
FEED_PAT=re.compile(r"(^|[-_])(product-feed|merchant-feed|shopping-feed|google-product-feed)([-_]|$)",re.I)

def challenge(s): return any(x in (s or "")[:30000].lower() for x in CHALLENGE_MARKERS)

def extract_assets(text):
    d={}
    for m in re.finditer(r"/wp-content/plugins/([^/?#'\"]+)",text or "",re.I):
        slug=re.sub(r"[^a-z0-9._-]","",m.group(1).lower())
        if slug: d.setdefault(slug,set())
    # plugin URLs seen in XHR may omit exact wp-content filename
    for m in re.finditer(r"(?:plugins|extensions)[/:]([a-z0-9][a-z0-9._-]{2,80})",text or "",re.I):
        slug=m.group(1).lower()
        if slug not in ("woocommerce","wordpress"): d.setdefault(slug,set())
    return sorted(d)

def families(assets, text, namespaces, xhr_urls):
    low=(text or "").lower()
    url_low="\n".join(xhr_urls).lower()
    ns=[str(x).lower() for x in namespaces]
    out={}
    for slug,fam in KNOWN.items():
        ev=[]
        if slug in assets: ev.append("plugin_asset:"+slug)
        if slug in low: ev.append("text_marker:"+slug)
        if slug in url_low: ev.append("xhr_url:"+slug)
        if any(x==slug or x.startswith(slug+"/") for x in ns): ev.append("wp_namespace:"+slug)
        if ev: out.setdefault(fam,[]).extend(ev)
    nsmap={"wpfm/v1":"wpfm_product_feed_manager","wppfm/v1":"wpfm_product_feed_manager"}
    for marker,fam in nsmap.items():
        if marker in ns: out.setdefault(fam,[]).append("namespace:"+marker)
    marker_map={
        "ctx_feed_webappick":("ctxfeed","webappick","woo-feed","woo_feed="),
        "adtribes_product_feed_pro":("woo-product-feed-pro","adtribes"),
        "woocommerce_google_product_feed":("woocommerce_gpf","woocommerce-google-product-feed"),
        "google_for_woocommerce":("google-listings-and-ads","google for woocommerce"),
        "wpfm_product_feed_manager":("product feed manager","wppfm","wpfm"),
    }
    for fam,marks in marker_map.items():
        for m in marks:
            if m in low or m in url_low: out.setdefault(fam,[]).append("marker:"+m)
    return [{"family":f,"confidence":"strong" if len(set(e))>=2 else "signal","evidence":sorted(set(e))}
            for f,e in sorted(out.items())]

def choose(fams):
    priority=["woocommerce_google_product_feed","ctx_feed_webappick","adtribes_product_feed_pro",
              "webtoffee_product_feed","wpfm_product_feed_manager","codesolz_feed","feedcraft","google_for_woocommerce"]
    for f in priority:
        if any(x["family"]==f for x in fams): return f
    return "unknown_woocommerce"

async def api_get(req,url,timeout=12000):
    try:
        r=await req.get(url,timeout=timeout,max_redirects=5,headers={
            "accept":"application/json,text/plain;q=.9,text/html;q=.8,*/*;q=.1",
            "user-agent":"Mozilla/5.0 (compatible; WooCommercePluginResearch/V175-derived)"
        })
        body=await r.text()
        return {"status":int(r.status),"url":str(r.url),"content_type":r.headers.get("content-type",""),
                "server":r.headers.get("server",""),"x_powered_by":r.headers.get("x-powered-by",""),
                "bytes":len(body),"challenge":challenge(body),"body":body}
    except PWTimeout:
        return {"status":0,"url":url,"content_type":"","bytes":0,"challenge":False,"transport":"timeout","body":""}
    except Exception as e:
        return {"status":0,"url":url,"content_type":"","bytes":0,"challenge":False,"transport":"error","error":str(e)[:240],"body":""}

async def run_site(name,root,pw):
    root=root.rstrip("/")
    browser=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    ctx=await browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
        locale="en-IN",viewport={"width":1440,"height":900},java_script_enabled=True)
    page=await ctx.new_page()
    xhr=[]
    async def on_response(resp):
        try:
            u=resp.url or ""; ct=(await resp.all_headers()).get("content-type","")
            ul=u.lower()
            interesting=("/wp-json/" in ul or "/api/" in ul or "/wp-content/plugins/" in ul or
                         "product-feed" in ul or "merchant" in ul or "shopping" in ul or
                         "google" in ul or "feed" in ul or "xml" in ul or "json" in ct.lower())
            if interesting and u not in {x["url"] for x in xhr}:
                xhr.append({"url":u,"status":int(resp.status),"content_type":ct})
        except Exception: pass
    page.on("response",on_response)
    out={"schema_version":"woocommerce-21-plugin-extraction/v1","source_extractor_version":VERSION,
         "site":name,"configured_root":root,"selected_origin":root,"status":"UNSET"}
    try:
        html=""
        try:
            resp=await page.goto(root,wait_until="domcontentloaded",timeout=30000)
            await page.wait_for_timeout(1200)
            html=await page.content()
            final=str(resp.url) if resp else root
            out["selected_origin"]=f"{urlparse(final).scheme}://{urlparse(final).netloc}"
            out["browser_homepage"]={"status":int(resp.status) if resp else 0,"final_url":final,
                                     "challenge":challenge(html),"html_bytes":len(html)}
        except Exception as e:
            out["browser_homepage"]={"status":0,"final_url":root,"challenge":False,"error":str(e)[:240]}
        origin=out["selected_origin"].rstrip("/")
        endpoint_defs=[
          ("wp-json","/wp-json/"),("rest-root","/?rest_route=/"),
          ("wp-v2","/wp-json/wp/v2/"),("rest-wp-v2","/?rest_route=/wp/v2/"),
          ("wc-v1-root","/wp-json/wc/v1/"),("wc-v2-root","/wp-json/wc/v2/"),("wc-v3-root","/wp-json/wc/v3/"),
          ("wc-v1-products-probe","/wp-json/wc/v1/products?per_page=1&_fields=id"),
          ("wc-v2-products-probe","/wp-json/wc/v2/products?per_page=1&_fields=id"),
          ("wc-v3-products-probe","/wp-json/wc/v3/products?per_page=1&_fields=id"),
          ("robots","/robots.txt"),
        ]
        ep_out=[]; bodies=[html]; namespaces=[]
        for name2,path in endpoint_defs:
            z=await api_get(page.request,origin+path)
            ep_out.append({k:z.get(k) for k in ("status","url","content_type","server","x_powered_by","bytes","challenge","transport") if z.get(k) is not None} | {"name":name2})
            if z["status"]==200 and z.get("body") and not z.get("challenge") and name2 not in {
                "wc-v1-products-probe","wc-v2-products-probe","wc-v3-products-probe"}:
                bodies.append(z["body"])
                try:
                    if "json" in z.get("content_type","").lower():
                        j=json.loads(z["body"])
                        if isinstance(j,dict):
                            if isinstance(j.get("namespaces"),list): namespaces.extend(map(str,j["namespaces"]))
                            namespaces.extend(str(k) for k in j.keys() if re.search(r"woo|feed|google|merchant|product|wpfm",str(k),re.I))
                except Exception: pass
        combined="\n".join(bodies)
        assets=extract_assets(combined+"\n"+"\n".join(x["url"] for x in xhr))
        fam=families(assets,combined,namespaces,[x["url"] for x in xhr])
        out.update({
          "public_endpoints":ep_out,
          "homepage_xhr":sorted(xhr,key=lambda x:x["url"]),
          "plugin_assets":assets,
          "feed_like_plugin_assets":[a for a in assets if (a in KNOWN or FEED_PAT.search(a)) and not DENY.match(a)],
          "feed_family_signals":fam,
          "primary_group":choose(fam),
          "public_api_namespaces":sorted(set(namespaces))[:150],
          "wordpress_generator":sorted(set(re.findall(r'<meta[^>]+(?:name|property)=["\']generator["\'][^>]+content=["\']([^"\']+)',html,re.I)))[:20],
        })
        if out["browser_homepage"].get("challenge"): out["status"]="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE"
        elif out["feed_family_signals"] or out["feed_like_plugin_assets"]: out["status"]="FEED_PLUGIN_SIGNALS_FOUND"
        elif out["plugin_assets"]: out["status"]="PLUGIN_SURFACE_RECOVERED_NO_FEED_SIGNAL"
        else: out["status"]="NO_PLUGIN_ASSETS_RECOVERED"
        return out
    finally:
        try: await ctx.close()
        except Exception: pass
        try: await browser.close()
        except Exception: pass

async def main():
    name=os.environ.get("SITE_NAME"); root=os.environ.get("SITE_ROOT")
    if not name or not root: raise SystemExit("SITE_NAME and SITE_ROOT required")
    outdir=Path(os.environ.get("OUT_DIR","out/plugin-extraction")); outdir.mkdir(parents=True,exist_ok=True)
    async with async_playwright() as pw:
        try:
            result=await asyncio.wait_for(run_site(name,root,pw),timeout=210)
        except Exception as e:
            result={"schema_version":"woocommerce-21-plugin-extraction/v1","source_extractor_version":VERSION,
                    "site":name,"configured_root":root,"selected_origin":root,"status":"RUNNER_ERROR","error":str(e)[:300]}
    (outdir/"fingerprint.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"site":result.get("site"),"status":result.get("status"),
                      "primary_group":result.get("primary_group"),"assets":len(result.get("plugin_assets",[])),
                      "xhr":len(result.get("homepage_xhr",[])),
                      "namespaces":len(result.get("public_api_namespaces",[]))},indent=2))
if __name__=="__main__": asyncio.run(main())
