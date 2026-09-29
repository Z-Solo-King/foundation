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
        ev=[("text_marker:"+m) for m in markers if m in low]
        if ev: out.setdefault(fam,[]).extend(ev)
    return [{"family":k,"confidence":"strong" if len(set(v))>=2 else "signal","evidence":sorted(set(v))} for k,v in sorted(out.items())]

async def get(req,url,timeout=15000):
    try:
        r=await req.get(url,timeout=timeout,max_redirects=5,headers={"accept":"text/html,application/json,text/plain;q=.9,*/*;q=.1","user-agent":"Mozilla/5.0 (compatible; WooCommercePluginResearch/V175)"})
        b=await r.text()
        return {"status":r.status,"url":str(r.url),"ct":r.headers.get("content-type",""),"body":b[:8*1024*1024],"challenge":blocked(b)}
    except PWTimeout: return {"status":0,"url":url,"ct":"","body":"","challenge":False,"transport":"timeout"}
    except Exception as e: return {"status":0,"url":url,"ct":"","body":"","challenge":False,"transport":"error","error":str(e)[:180]}

async def one(name,root,pw,sem):
    async with sem:
        b=await pw.chromium.launch(headless=True,args=["--no-sandbox","--disable-dev-shm-usage"])
        c=await b.new_context(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",locale="en-IN",viewport={"width":1440,"height":900})
        p=await c.new_page(); root=root.rstrip("/")
        out={"schema_version":"woocommerce-22-plugin-browser-recovery/v1","source_extractor_version":SOURCE_EXTRACTOR_VERSION,"site":name,"configured_root":root}
        try:
            r=await p.goto(root,wait_until="domcontentloaded",timeout=30000); await p.wait_for_timeout(1200)
            html=await p.content()
            final=str(r.url) if r else root; out["selected_origin"]=f"{urlparse(final).scheme}://{urlparse(final).netloc}"
            out["browser"]={"status":int(r.status) if r else 0,"final_url":final,"challenge":blocked(html),"html_bytes":len(html)}
        except Exception as e:
            html=""; out["selected_origin"]=root; out["browser"]={"status":0,"final_url":root,"challenge":False,"goto_error":str(e)[:220]}
        bodies=[html]; namespaces=[]; endpoints=[]
        for path in ("/wp-json/","/?rest_route=/","/robots.txt"):
            u=out["selected_origin"].rstrip("/") + path; z=await get(p.request,u)
            endpoints.append({"path":path,"status":z["status"],"final_url":z["url"],"content_type":z["ct"],"bytes":len(z["body"]),"challenge":z["challenge"],"transport":z.get("transport","ok")})
            if z["status"]==200 and z["body"] and not z["challenge"]:
                bodies.append(z["body"])
                if path!="/robots.txt":
                    try:
                        j=json.loads(z["body"]); namespaces += [str(x) for x in (j.get("namespaces") or [])]
                        namespaces += [str(k) for k in j.keys() if re.search(r"feed|google|merchant|product",str(k),re.I)]
                    except Exception: pass
        combined="\n".join(bodies); pa=assets(combined)
        out["public_endpoints"]=endpoints; out["plugin_assets"]=pa
        out["feed_like_plugin_assets"]=[x for x in pa if ("feed" in x and not DENY.match(x)) or x in KNOWN]
        out["feed_family_signals"]=family_hits(pa,combined,namespaces)
        out["public_api_namespaces"]=sorted(set(namespaces))[:100]
        gens=re.findall(r'<meta[^>]+(?:name|property)=[\"\']generator[\"\'][^>]+content=[\"\']([^\"\']+)',html,re.I)
        out["wordpress_generator"]=sorted(set(gens))[:20]
        out["identity_tokens"]=sorted(set(re.sub(r"[^a-z0-9]+"," ",name.lower()).split()+re.sub(r"[^a-z0-9]+"," ",urlparse(root).hostname.lower()).split()))[:20]
        if out["browser"].get("challenge"): out["status"]="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE"
        elif out["plugin_assets"]: out["status"]="FEED_PLUGIN_SIGNALS_FOUND" if (out["feed_like_plugin_assets"] or out["feed_family_signals"]) else "PLUGIN_SURFACE_RECOVERED_NO_FEED_SIGNAL"
        else: out["status"]="BROWSER_REACHED_NO_PLUGIN_ASSETS"
        await b.close()
        return out

async def main():
    outdir=Path(os.environ.get("OUT_DIR","out/plugin-browser-recovery")); outdir.mkdir(parents=True,exist_ok=True)
    sem=asyncio.Semaphore(int(os.environ.get("BROWSER_CONCURRENCY","4")))
    async with async_playwright() as pw:
        results=await asyncio.gather(*(one(n,u,pw,sem) for n,u in SITES))
    payload={"schema_version":"woocommerce-22-plugin-browser-recovery/v1","source_extractor_version":SOURCE_EXTRACTOR_VERSION,
      "policy":"Public read-only plugin evidence recovery. No product APIs, no feed URL mining from HTML/JS/XHR, no CAPTCHA solving, no Cloudflare challenge bypass, no clearance-cookie replay, no authentication or stealth/evasion.",
      "site_count":len(results),"results":sorted(results,key=lambda x:x["site"].lower())}
    (outdir/"recovery.json").write_text(json.dumps(payload,indent=2)+"\n",encoding="utf-8")
    lines=["# 22-site plugin browser recovery","","| Site | Status | Feed family signals | Feed-like assets | Plugin assets |","|---|---|---|---|---:|"]
    for r in payload["results"]:
        lines.append(f'| {r["site"]} | {r["status"]} | {", ".join(x["family"] for x in r["feed_family_signals"]) or "none"} | {", ".join(r["feed_like_plugin_assets"]) or "none"} | {len(r["plugin_assets"])} |')
    (outdir/"recovery.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"site_count":len(results),"feed_signal_sites":sum(bool(r["feed_family_signals"] or r["feed_like_plugin_assets"]) for r in results),
      "browser_challenge_sites":sum(r["status"]=="BROWSER_CHALLENGE_NO_PLUGIN_SURFACE" for r in results),
      "reached_with_plugin_assets":sum(bool(r["plugin_assets"]) for r in results)},indent=2))
if __name__=="__main__": asyncio.run(main())
