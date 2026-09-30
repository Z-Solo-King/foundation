#!/usr/bin/env python3
from __future__ import annotations
import asyncio, json, os, re
from pathlib import Path
from urllib.parse import urlparse, urlencode
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

EXTRACTOR="V175-derived-browser-plugin-extractor"
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
("Viper PC","https://viperpc.in"),("hotshiftpc","https://hotshiftpc.com"),("ithunt","https://ithunt.in"),
]
TARGET_NAMES=dict(SITES)
CHALLENGE_MARKERS=("just a moment","cf-chl-","cf-turnstile","checking your browser","verify you are human",
"attention required","access denied","checking your browser","enable javascript and cookies","captcha","challenge-platform")
PLUGIN_RE=re.compile(r"/wp-content/plugins/([^/?#'\\]+)",re.I)
FEED_ALLOW=re.compile(r"(?:^|[-_])(feed|product-feed|merchant-feed|shopping-feed|google-product-feed)(?:$|[-_])|^(?:woo-feed|woo-product-feed-pro|product-feed-manager|wppfm|google-listings-and-ads|merchant-feed-booster-lite-for-woocommerce|thebasics-product-feed|ctx-feed|webappick-product-feed-for-woocommerce)$",re.I)
FEED_DENY=re.compile(r"^(?:instagram-feed|advanced-ads|facebook-for-woocommerce|feedzy-rss-feeds)$",re.I)
KNOWN_NS={"wpfm/v1":"wpfm_product_feed_manager","wppfm/v1":"wpfm_product_feed_manager"}

def challenge(text): return any(m in (text or "")[:40000].lower() for m in CHALLENGE_MARKERS)

def plugin_assets(text):
    found={}
    for m in PLUGIN_RE.finditer(text or ""):
        slug=re.sub(r"[^a-z0-9._-]","",m.group(1).lower())
        if slug: found[slug]=1
    return sorted(found)

def feed_assets(a): return [x for x in a if FEED_ALLOW.search(x) and not FEED_DENY.match(x)][:100]

def namespaces(body):
    try:
        j=json.loads(body); vals=[]
        if isinstance(j,dict):
            vals.extend([str(x) for x in (j.get("namespaces") or [])])
            vals.extend([str(k) for k in j if re.search(r"woo|feed|google|merchant|product",str(k),re.I)])
        return sorted(set(vals))[:300]
    except Exception: return []

def family_signals(text,nss,xhr_urls):
    low=(text or "").lower(); hits={}
    markers={
      "ctx_feed_webappick":("ctxfeed","webappick","ctx-feed","woo-feed","woo_feed="),
      "adtribes_product_feed_pro":("woo-product-feed-pro","adtribes","woosea"),
      "woocommerce_google_product_feed":("woocommerce_gpf","woocommerce-google-product-feed"),
      "webtoffee_product_feed":("webtoffee_product_feed","webtoffee"),
      "wpfm_product_feed_manager":("wppfm","product feed manager","wpfm"),
      "codesolz_feed":("codesolz","codesolz-feeds"),
      "feedcraft":("feedcraft-product-feed","feedcraft product feed"),
      "google_for_woocommerce":("google-listings-and-ads","google for woocommerce","google merchant api"),
    }
    for fam,ms in markers.items():
        ev=[m for m in ms if m in low]
        if ev: hits.setdefault(fam,set()).update("text:"+m for m in ev)
    for ns in nss:
        n=ns.lower()
        for marker,fam in KNOWN_NS.items():
            if n==marker or n.startswith(marker+"/"): hits.setdefault(fam,set()).add("namespace:"+ns)
    for u in xhr_urls:
        ul=u.lower()
        for fam,ms in markers.items():
            if any(m in ul for m in ms): hits.setdefault(fam,set()).add("xhr:"+next(m for m in ms if m in ul))
    return [{"family":f,"confidence":"strong" if len(e)>=2 else "signal","evidence":sorted(e)} for f,e in sorted(hits.items())]

def classify_api_url(u):
    p=urlparse(u); path=p.path.lower()
    if "/wp-json/wc/v1" in path: return "woocommerce_rest_v1"
    if "/wp-json/wc/v2" in path: return "woocommerce_rest_v2"
    if "/wp-json/wc/v3" in path: return "woocommerce_rest_v3"
    if "rest_route=/wc/v1" in (p.query or "").lower(): return "rest_route_wc_v1"
    if "rest_route=/wc/v2" in (p.query or "").lower(): return "rest_route_wc_v2"
    if "rest_route=/wc/v3" in (p.query or "").lower(): return "rest_route_wc_v3"
    if "/wp-json/wp/v2" in path: return "wordpress_rest_wp_v2"
    if "/wp-json" in path or "rest_route=/" in (p.query or "").lower(): return "wordpress_rest"
    return ""

async def req_get(req,u,timeout=15000):
    try:
        r=await req.get(u,timeout=timeout,max_redirects=5,headers={"accept":"application/json,text/html,text/plain;q=.9,*/*;q=.1","user-agent":"Mozilla/5.0 (compatible; WooCommercePluginResearch/V175-derived)"})
        body=await r.text()
        return {"status":int(r.status),"final_url":str(r.url),"ct":r.headers.get("content-type",""),"server":r.headers.get("server",""),"x_powered_by":r.headers.get("x-powered-by",""),"bytes":len(body),"challenge":challenge(body),"body":body[:6*1024*1024]}
    except PlaywrightTimeoutError: return {"status":0,"final_url":u,"ct":"","server":"","x_powered_by":"","bytes":0,"challenge":False,"transport":"timeout","body":""}
    except Exception as e: return {"status":0,"final_url":u,"ct":"","server":"","x_powered_by":"","bytes":0,"challenge":False,"transport":"error","error":str(e)[:240],"body":""}

async def req_options(req,u,timeout=10000):
    try:
        r=await req.fetch(u,method="OPTIONS",timeout=timeout,max_redirects=5,headers={"origin":u,"access-control-request-method":"GET","user-agent":"Mozilla/5.0 (compatible; WooCommercePluginResearch/V175-derived)"})
        return {"status":int(r.status),"allow":r.headers.get("allow",""),"link":r.headers.get("link",""),"ct":r.headers.get("content-type",""),"challenge":False}
    except PlaywrightTimeoutError: return {"status":0,"allow":"","link":"","ct":"","challenge":False,"transport":"timeout"}
    except Exception as e: return {"status":0,"allow":"","link":"","ct":"","challenge":False,"transport":"error","error":str(e)[:240]}

async def extract(name,root,outdir):
    outdir=Path(outdir); outdir.mkdir(parents=True,exist_ok=True); root=root.rstrip("/")
    result={"schema_version":"woocommerce-21-plugin-extraction/v1","extractor":EXTRACTOR,"site":name,"configured_root":root,
            "selected_origin":root,"status":"UNSET","homepage":{}, "plugin_assets":[],"feed_like_plugin_assets":[],
            "feed_family_signals":[],"public_api_namespaces":[],"xhr":[], "rest_probes":[],"product_api_options":[]}
    async with async_playwright() as pw:
        browser=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        ctx=await browser.new_context(
          user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
          locale="en-IN",viewport={"width":1440,"height":900},java_script_enabled=True)
        page=await ctx.new_page()
        xhr=[]
        async def on_response(resp):
            try:
                rt=resp.request.resource_type
                if rt not in ("xhr","fetch"): return
                u=resp.url
                if any(m in u.lower() for m in (".png",".jpg",".jpeg",".gif",".webp",".svg",".woff",".woff2",".css",".js")):
                    return
                xhr.append({"url":u,"method":resp.request.method,"status":int(resp.status),
                            "resource_type":rt,"content_type":resp.headers.get("content-type","")})
            except Exception: pass
        page.on("response",on_response)
        try:
            r=await page.goto(root,wait_until="domcontentloaded",timeout=35000)
            await page.wait_for_timeout(1800)
            html=await page.content()
            final=str(r.url) if r else root
            result["selected_origin"]=f"{urlparse(final).scheme}://{urlparse(final).netloc}"
            result["homepage"]={"status":int(r.status) if r else 0,"final_url":final,"challenge":challenge(html),"html_bytes":len(html)}
            # Performance API catches AJAX calls that Playwright response hooks can miss.
            try:
                perf=await page.evaluate("""() => performance.getEntriesByType('resource').map(x=>x.name).filter(u=>/^https?:/i.test(u))""")
                for u in perf:
                    if classify_api_url(u) and not any(x["url"]==u for x in xhr):
                        xhr.append({"url":u,"method":"GET","status":0,"resource_type":"performance","content_type":""})
            except Exception: pass
        except Exception as e:
            html=""; result["homepage"]={"status":0,"final_url":root,"challenge":False,"error":str(e)[:240]}
        base=result["selected_origin"]
        api_paths=[
          "/wp-json/","/?rest_route=/","/wp-json/wp/v2/","/?rest_route=/wp/v2/",
          "/wp-json/wc/v1","/wp-json/wc/v2","/wp-json/wc/v3",
          "/?rest_route=/wc/v1","/?rest_route=/wc/v2","/?rest_route=/wc/v3",
        ]
        bodies=[html]; all_ns=set()
        for p in api_paths:
            z=await req_get(page.request,base+p)
            row={"path":p,"status":z["status"],"final_url":z["final_url"],"content_type":z["ct"],"bytes":z["bytes"],
                 "challenge":z["challenge"],"transport":z.get("transport","ok")}
            if z.get("server"): row["server"]=z["server"]
            if z.get("x_powered_by"): row["x_powered_by"]=z["x_powered_by"]
            result["rest_probes"].append(row)
            if z["status"] in (200,301,302,401,403) and z.get("body") and not z["challenge"]:
                if p.startswith("/wp-json/") or "rest_route" in p:
                    bodies.append(z["body"])
                    all_ns.update(namespaces(z["body"]))
        # Product API v1/v2/v3 probes. Request the smallest public shape and retain only metadata.
        for v in ("v1","v2","v3"):
            u=base+f"/wp-json/wc/{v}/products?per_page=1&_fields=id"
            o=await req_options(page.request,base+f"/wp-json/wc/{v}/products")
            g=await req_get(page.request,u,timeout=12000)
            result["product_api_options"].append({
                "version":v,"url":u,
                "options":o,
                "get_status":g["status"],
                "get_final_url":g["final_url"],
                "get_content_type":g["ct"],
                "get_bytes":g["bytes"],
                "get_challenge":g["challenge"],
                "get_transport":g.get("transport","ok"),
                "get_response_markers":sorted(set(re.findall(
                    r"wpfm|wppfm|feed|google|merchant|product|woocommerce",g.get("body",""),re.I
                )))[:40],
            })
        result["xhr"]=sorted({(x["url"],x["method"],x["status"]):(x) for x in xhr}.values(),key=lambda x:x["url"])[:500]
        combined="\n".join(bodies)
        assets=plugin_assets(combined+json.dumps(result["xhr"]))
        result["plugin_assets"]=assets
        result["feed_like_plugin_assets"]=feed_assets(assets)
        result["public_api_namespaces"]=sorted(all_ns)[:300]
        result["feed_family_signals"]=family_signals(combined,sorted(all_ns),[x["url"] for x in result["xhr"]])
        if result["homepage"].get("challenge"): result["status"]="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE"
        elif result["plugin_assets"]: result["status"]="PLUGIN_SURFACE_RECOVERED"
        else: result["status"]="BROWSER_REACHED_NO_PLUGIN_ASSETS"
        await ctx.close(); await browser.close()
    (outdir/"recovery.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    summary={"site":name,"status":result["status"],"plugin_assets":len(result["plugin_assets"]),
             "feed_like_plugin_assets":result["feed_like_plugin_assets"],
             "feed_family_signals":result["feed_family_signals"],
             "xhr_api_events":sum(bool(classify_api_url(x["url"])) for x in result["xhr"]),
             "wc_v1_v2_v3":{x["version"]:x.get("get_status", x.get("options",{}).get("status", 0))
                            for x in result["product_api_options"]}}
    print(json.dumps(summary,indent=2))
    return result

async def main():
    name=os.environ["SITE_NAME"]; root=os.environ["SITE_ROOT"]; out=os.environ.get("OUT_DIR","out/site")
    try:
        await extract(name,root,out)
    except Exception as exc:
        outdir=Path(out); outdir.mkdir(parents=True,exist_ok=True)
        error={
            "schema_version":"woocommerce-21-plugin-extraction/v1",
            "extractor":EXTRACTOR,
            "site":name,
            "configured_root":root,
            "selected_origin":root,
            "status":"EXTRACTOR_RUNTIME_ERROR",
            "error":str(exc)[:1000],
            "homepage":{},
            "plugin_assets":[],
            "feed_like_plugin_assets":[],
            "feed_family_signals":[],
            "public_api_namespaces":[],
            "xhr":[],
            "rest_probes":[],
            "product_api_options":[]
        }
        (outdir/"recovery.json").write_text(json.dumps(error,indent=2)+"\n",encoding="utf-8")
        print(json.dumps({"site":name,"status":error["status"],"error":error["error"]},indent=2))
        return 0

if __name__=="__main__": asyncio.run(main())
