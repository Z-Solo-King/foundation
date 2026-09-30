#!/usr/bin/env python3
import asyncio, json, os, re
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright, TimeoutError as PWTimeout

SOURCE_EXTRACTOR_VERSION = "V175"
SITES = [
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
("itgadgetsonline","https://itgadgetsonline.com"),("ithunt","https://ithunt.in"),
]
CHALLENGE = ("just a moment","cf-chl-","cf-browser-verification","cf-mitigated","managed_challenge",
"attention required","checking your browser","enable javascript and cookies","verify you are human",
"cf-turnstile","captcha","challenge-platform")
KNOWN = {
"woocommerce-google-product-feed":"woocommerce_google_product_feed","woo-feed":"ctx_feed_webappick",
"webappick-product-feed-for-woocommerce":"ctx_feed_webappick","ctx-feed":"ctx_feed_webappick",
"woo-product-feed-pro":"adtribes_product_feed_pro","merchant-feed-booster-lite-for-woocommerce":"codesolz_feed",
"thebasics-product-feed":"feedcraft","product-feed-manager":"wpfm_product_feed_manager",
"wppfm":"wpfm_product_feed_manager","google-listings-and-ads":"google_for_woocommerce",
}
DENY = re.compile(r"^(instagram-feed|facebook-for-woocommerce|advanced-ads|feedzy-rss-feeds)$",re.I)

def blocked(text): return any(x in (text or "")[:30000].lower() for x in CHALLENGE)

def assets(text):
    d={}
    rx=re.compile(r"/wp-content/plugins/([^/?\"'#\\]+)",re.I)
    for m in rx.finditer(text or ""):
        s=re.sub(r"[^a-z0-9._-]","",m.group(1).lower())
        if s: d[s]=1
    return sorted(d)

def family_hits(a, text, namespaces):
    low=(text or "").lower(); out={}
    for slug,fam in KNOWN.items():
        ev=[]
        if slug in a: ev.append("plugin_asset:"+slug)
        if slug in low: ev.append("text_marker:"+slug)
        if any(slug in str(n).lower() for n in namespaces): ev.append("wp_namespace:"+slug)
        if ev: out.setdefault(fam,[]).extend(ev)
    for fam, markers in {
        "ctx_feed_webappick":("ctxfeed","webappick","woo_feed="),
        "adtribes_product_feed_pro":("woo-product-feed-pro","adtribes"),
        "woocommerce_google_product_feed":("woocommerce_gpf","woocommerce-google-product-feed"),
        "google_for_woocommerce":("google-listings-and-ads","google for woocommerce"),
    }.items():
        ev=["text_marker:"+m for m in markers if m in low]
        if ev: out.setdefault(fam,[]).extend(ev)
    return [{"family":k,"confidence":"strong" if len(set(v))>=2 else "signal","evidence":sorted(set(v))} for k,v in sorted(out.items())]

async def get(req,url,timeout=12000):
    try:
        r=await req.get(url,timeout=timeout,max_redirects=5,headers={
            "accept":"text/html,application/json,text/plain;q=.9,*/*;q=.1",
            "user-agent":"Mozilla/5.0 (compatible; WooCommercePluginResearch/V175)"
        })
        b=await r.text()
        return {"status":int(r.status),"url":str(r.url),"ct":r.headers.get("content-type",""),
                "body":b[:8*1024*1024],"challenge":blocked(b)}
    except PWTimeout:
        return {"status":0,"url":url,"ct":"","body":"","challenge":False,"transport":"timeout"}
    except Exception as e:
        return {"status":0,"url":url,"ct":"","body":"","challenge":False,"transport":"error","error":str(e)[:180]}

async def one(name,root,pw):
    root=root.rstrip("/")
    browser=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
    context=await browser.new_context(
        user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
        locale="en-IN",viewport={"width":1440,"height":900})
    page=await context.new_page()
    out={"schema_version":"woocommerce-22-plugin-browser-recovery/v3","source_extractor_version":SOURCE_EXTRACTOR_VERSION,
         "site":name,"configured_root":root,"selected_origin":root}
    try:
        try:
            r=await page.goto(root,wait_until="domcontentloaded",timeout=30000)
            await page.wait_for_timeout(1000)
            final=str(r.url) if r else root
            html=await page.content()
            out["selected_origin"]=f"{urlparse(final).scheme}://{urlparse(final).netloc}"
            out["browser"]={"status":int(r.status) if r else 0,"final_url":final,"challenge":blocked(html),"html_bytes":len(html)}
        except Exception as e:
            html=""
            out["browser"]={"status":0,"final_url":root,"challenge":False,"goto_error":str(e)[:220]}
        bodies=[html]; namespaces=[]; endpoints=[]
        for path in ("/wp-json/","/?rest_route=/","/robots.txt"):
            u=out["selected_origin"].rstrip("/") + path
            z=await get(page.request,u)
            endpoints.append({"path":path,"status":z["status"],"final_url":z["url"],"content_type":z["ct"],
                              "bytes":len(z["body"]),"challenge":z["challenge"],"transport":z.get("transport","ok")})
            if z["status"]==200 and z["body"] and not z["challenge"]:
                bodies.append(z["body"])
                if path!="/robots.txt":
                    try:
                        j=json.loads(z["body"])
                        namespaces += [str(x) for x in (j.get("namespaces") or [])]
                        namespaces += [str(k) for k in j.keys() if re.search(r"feed|google|merchant|product",str(k),re.I)]
                    except Exception: pass
        # Some stores expose a cleaner public theme on catalog pages while the home page is challenged.
        page_paths=["/shop/","/store/","/products/"]
        page_results=[]
        for page_path in page_paths:
            u=out["selected_origin"].rstrip("/") + page_path
            try:
                pr=await page.goto(u,wait_until="domcontentloaded",timeout=15000)
                await page.wait_for_timeout(500)
                ph=await page.content()
                page_results.append({"path":page_path,"status":int(pr.status) if pr else 0,
                    "final_url":str(pr.url) if pr else u,"challenge":blocked(ph),"html_bytes":len(ph)})
                if pr and pr.status==200 and ph and not blocked(ph):
                    bodies.append(ph)
            except Exception as e:
                page_results.append({"path":page_path,"status":0,"final_url":u,"challenge":False,
                    "transport":"error","error":str(e)[:180]})
        combined="\n".join(bodies); pa=assets(combined)
        out["public_endpoints"]=endpoints; out["public_page_recovery"]=page_results; out["plugin_assets"]=pa
        out["feed_like_plugin_assets"]=[x for x in pa if not DENY.match(x) and (
            x in KNOWN or bool(re.search(r"(^|[-_])(product-feed|merchant-feed|shopping-feed|google-product-feed)([-_]|$)",x,re.I)))]
        out["feed_family_signals"]=family_hits(pa,combined,namespaces)
        out["public_api_namespaces"]=sorted(set(namespaces))[:100]
        out["wordpress_generator"]=sorted(set(re.findall(
            r'<meta[^>]+(?:name|property)=["\']generator["\'][^>]+content=["\']([^"\']+)',html,re.I)))[:20]
        out["identity_tokens"]=sorted(set(re.sub(r"[^a-z0-9]+"," ",name.lower()).split()+
                                           re.sub(r"[^a-z0-9]+"," ",urlparse(root).hostname.lower()).split()))[:20]
        if out["browser"].get("challenge"):
            out["status"]="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE"
        elif out["plugin_assets"]:
            out["status"]="FEED_PLUGIN_SIGNALS_FOUND" if (out["feed_like_plugin_assets"] or out["feed_family_signals"]) else "PLUGIN_SURFACE_RECOVERED_NO_FEED_SIGNAL"
        else:
            out["status"]="BROWSER_REACHED_NO_PLUGIN_ASSETS"
        return out
    finally:
        try: await context.close()
        except Exception: pass
        try: await browser.close()
        except Exception: pass

async def main():
    wanted_name=os.environ.get("SITE_NAME","").strip()
    wanted_root=os.environ.get("SITE_ROOT","").strip()
    sites=[(wanted_name,wanted_root)] if wanted_name and wanted_root else SITES
    outdir=Path(os.environ.get("OUT_DIR","out/plugin-browser-recovery")); outdir.mkdir(parents=True,exist_ok=True)
    sem=asyncio.Semaphore(1 if len(sites)==1 else int(os.environ.get("BROWSER_CONCURRENCY","4")))
    async with async_playwright() as pw:
        async def run(s):
            async with sem:
                try: return await asyncio.wait_for(one(s[0],s[1],pw),timeout=float(os.environ.get("SITE_TIMEOUT","180")))
                except Exception as e:
                    return {"schema_version":"woocommerce-22-plugin-browser-recovery/v2","source_extractor_version":SOURCE_EXTRACTOR_VERSION,
                            "site":s[0],"configured_root":s[1],"selected_origin":s[1],"status":"RECOVERY_RUNNER_ERROR","error":str(e)[:300]}
        results=await asyncio.gather(*(run(s) for s in sites))
    payload={"schema_version":"woocommerce-22-plugin-browser-recovery/v2","source_extractor_version":SOURCE_EXTRACTOR_VERSION,
      "policy":"Public read-only plugin evidence recovery. No product APIs, no feed URL mining from HTML/JS/XHR, no CAPTCHA solving, no Cloudflare challenge bypass, no clearance-cookie replay, no authentication or stealth/evasion.",
      "site_count":len(results),"results":sorted(results,key=lambda x:x["site"].lower())}
    (outdir/"recovery.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    lines=["# 22-site plugin browser recovery","","| Site | Status | Feed family signals | Feed-like assets | Plugin assets |","|---|---|---|---|---:|"]
    for r in payload["results"]:
        lines.append(f'| {r["site"]} | {r["status"]} | {", ".join(x["family"] for x in r.get("feed_family_signals",[])) or "none"} | {", ".join(r.get("feed_like_plugin_assets",[])) or "none"} | {len(r.get("plugin_assets",[]))} |')
    (outdir/"recovery.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"site_count":len(results),
      "feed_signal_sites":sum(bool(r.get("feed_family_signals") or r.get("feed_like_plugin_assets")) for r in results),
      "browser_challenge_sites":sum(r.get("status")=="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE" for r in results),
      "reached_with_plugin_assets":sum(bool(r.get("plugin_assets")) for r in results)},indent=2))

if __name__=="__main__": asyncio.run(main())
