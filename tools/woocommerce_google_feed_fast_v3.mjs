import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { chromium } from "playwright";

const TARGETS = [
  ["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["avikaretails","https://avikaretails.com"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
  ["GamesNComps","https://gamesncomps.com"],["Geekbees","https://geekbees.in"],["hotshiftpc","https://hotshiftpc.com"],["itgadgetsonline","https://itgadgetsonline.com"],
  ["ithunt","https://ithunt.in"],["kccomputers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["Kryptronix Gaming","https://kryptronix.in"],
  ["NCL Computer","https://nclcomputer.com"],["networkitstore","https://networkitstore.in"],["nexusinfosys","https://www.mynexusinfosys.com"],
  ["PC Kumar Infotech","https://pckumar.in"],["PC Studio","https://www.pcstudio.in"],["PCHubShop","https://www.pchubshop.com"],["Prime ABGB","https://www.primeabgb.com"],
  ["quickincomputers","https://quickincomputers.com"],["SCL Gaming","https://sclgaming.in"],["solankienterprises","https://solankienterprises.com"],["Variety Infotech","https://varietyinfotech.com"],
  ["Viper PC","https://viperpc.in"],["AULA India","https://aulaindia.com"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],
  ["Moskeys","https://moskeys.com"],["Ninja Dog","https://ninjadog.in"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"]
];

const PRIMARY = [
  "/?woocommerce_gpf=google","/woocommerce_gpf/google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
  "/google-products.xml","/google-product-feed.xml"
];
const PLUGIN = [
  "/google.xml","/google_feed.xml","/google_base.xml","/google-shopping.xml","/google-shopping-feed.xml",
  "/product-feed.xml","/products-feed.xml","/merchant-feed.xml","/feed/google.xml","/feed/google-products.xml",
  "/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml",
  "/feed.xml","/rss.xml","/products.rss","/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/json",
  "/wp-content/uploads/woo-feed/google/xml/google.xml","/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/wppfm-feeds/google.xml"
];

const TARGET_START = Math.max(0, Number.parseInt(process.env.TARGET_START || "0",10) || 0);
const TARGET_COUNT = Math.max(1, Number.parseInt(process.env.TARGET_COUNT || "8",10) || 8);
const SELECTED = TARGETS.slice(TARGET_START, TARGET_START + TARGET_COUNT);
const UA = "Mozilla/5.0 (compatible; WooCommerceGoogleFastV2/1.0)";
const TIMEOUT_MS = 12000;
await mkdir("out/fast2/feeds",{recursive:true});

const sleep = ms => new Promise(r => setTimeout(r, ms));
const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,70)||"site";

function challenge(status, text="") {
  const x = String(text).slice(0,12000).toLowerCase();
  return [403,429,430,451,503,520,521,522,523,524].includes(status) &&
    /just a moment|cf-chl|cloudflare|challenge-platform|cf-turnstile|captcha|verify you are human|access denied|request blocked|attention required|checking your browser/.test(x);
}
function sameOrigin(url, base) { try { return new URL(url).origin === new URL(base).origin; } catch { return false; } }
function sourceXml(body) {
  const s = String(body||"");
  const m = s.match(/id="webkit-xml-viewer-source-xml">([\s\S]*?)<\/div>/i);
  if (!m) return s;
  return m[1].replace(/&lt;/g,"<").replace(/&gt;/g,">").replace(/&amp;/g,"&").replace(/&quot;/g,'"').replace(/&#39;/g,"'");
}
function validate(body, ct="") {
  const s = sourceXml(body);
  const root = /^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)/i.test(s);
  const ns = /xmlns(?::[\w.-]+)?\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(s);
  const records = [...s.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].map(m=>m[1]);
  if (!records.length) return {qualifies:false,item_count:0,coverage:0,google_namespace:ns,content_type:ct};
  let present=0;
  for (const b of records) {
    present += Number(/<(?:[\w.-]+:)?id\b[^>]*>/i.test(b));
    present += Number(/<title\b[^>]*>/i.test(b));
    present += Number(/<link\b[^>]*>/i.test(b));
    present += Number(/<(?:[\w.-]+:)?price\b[^>]*>/i.test(b));
  }
  const coverage = present / (records.length * 4);
  return {qualifies:Boolean(root&&ns&&coverage>=0.75),item_count:records.length,coverage:Number(coverage.toFixed(4)),google_namespace:ns,content_type:ct};
}
async function get(url) {
  const ac = new AbortController();
  const timer = setTimeout(()=>ac.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
      "User-Agent":UA,"Accept":"application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2"
    }});
    const buf=Buffer.from(await r.arrayBuffer());
    return {status:r.status,url:r.url,ct:r.headers.get("content-type")||"",buf,text:buf.length<60*1024*1024?buf.toString("utf8"):"",bytes:buf.length};
  } finally { clearTimeout(timer); }
}
async function probeList(urls, out, stopOnFeed=true) {
  let cursor=0;
  const worker=async()=>{
    while (cursor<urls.length && (!stopOnFeed || !out.feed)) {
      const url=urls[cursor++];
      try {
        const r=await get(url);
        if(r.status===200){
          const v=validate(r.text,r.ct);
          if(v.qualifies){
            const hash=createHash("sha256").update(r.buf).digest("hex");
            const file=`out/fast2/feeds/${slug(out.name)}-${hash.slice(0,12)}.xml`;
            await writeFile(file,r.buf);
            out.feed={url,finalUrl:r.url,source:"public_probe",file,sha256:hash,bytes:r.bytes,...v};
            out.probes.push({url,status:r.status,classification:"LIVE_VERIFIED",...v});
            continue;
          }
          out.probes.push({url,status:r.status,classification:"NO_MATCH",...v});
        } else {
          out.probes.push({url,status:r.status,classification:challenge(r.status,r.text)?"BLOCKED_OR_CHALLENGED":r.status===401?"AUTH_REQUIRED":r.status===403?"ACCESS_DENIED":r.status===429?"RATE_LIMITED":`HTTP_${r.status}`});
        }
      } catch(e) {
        out.probes.push({url,classification:e?.name==="AbortError"?"TIMEOUT":"ERROR",error:e?.name||String(e)});
      }
    }
  };
  await Promise.all(Array.from({length:Math.min(8,urls.length)},worker));
}
async function browserDiscover(base,out) {
  let browser;
  try {
    browser=await chromium.launch({headless:true,args:["--disable-dev-shm-usage"]});
    const page=await browser.newPage({userAgent:UA,locale:"en-IN"});
    const seen=new Map();
    page.on("response",async res=>{
      try{
        const u=res.url();
        if(!sameOrigin(u,base)) return;
        const ct=(res.headers()["content-type"]||"").toLowerCase();
        if(!/(xml|rss|atom|json)/.test(ct) && !/(google|merchant|shopping|feed|product)/i.test(u)) return;
        if(!/(google|merchant|shopping|feed|product)/i.test(u)) return;
        if(!seen.has(u)) seen.set(u,{url:u,status:res.status(),ct});
      }catch{}
    });
    const nav=await page.goto(base,{waitUntil:"domcontentloaded",timeout:20000}).catch(()=>null);
    out.browser_status=nav?.status()||0;
    await sleep(3000);
    for (const u of [...seen.keys()].slice(0,40)) {
      if(out.feed) break;
      try {
        const r=await get(u);
        if(r.status===200){
          const v=validate(r.text,r.ct);
          out.browser_hits.push({url:u,status:r.status,validation:v});
          if(v.qualifies){
            const hash=createHash("sha256").update(r.buf).digest("hex");
            const file=`out/fast2/feeds/${slug(out.name)}-${hash.slice(0,12)}.xml`;
            await writeFile(file,r.buf);
            out.feed={url:u,finalUrl:r.url,source:"browser_xhr",file,sha256:hash,bytes:r.bytes,...v};
            break;
          }
        }
      }catch{}
    }
  } catch(e) { out.browser_error=e?.name||String(e); }
  finally { try{await browser?.close();}catch{} }
}
async function historyFallback(base,out) {
  try {
    const host=new URL(base).hostname;
    const u=`https://web.archive.org/cdx/search/cdx?url=${encodeURIComponent(host+"/*")}&output=json&fl=original&filter=statuscode:200&collapse=urlkey&limit=120`;
    const r=await get(u);
    if(r.status!==200) return;
    const d=JSON.parse(r.text), rows=Array.isArray(d)?d.slice(1):[];
    const urls=[...new Set(rows.map(x=>x?.[0]).filter(u=>typeof u==="string" && (/\.xml(?:[?#]|$)/i.test(u)||/(?:google|merchant|shopping|product-feed|woo-feed|wppfm|feedcraft|codesolz)/i.test(u)) && !/\/product\//i.test(u)))].slice(0,20);
    out.history_candidates=urls;
    if(urls.length) await probeList(urls,out,true);
  } catch{}
}
async function scan([name,base]) {
  const out={name,base,feed:null,probes:[],browser_hits:[],history_candidates:[],fingerprints:[]};
  const [home,rest]=await Promise.all([get(base+"/").catch(e=>({error:e?.name||String(e)})),get(base+"/wp-json/").catch(e=>({error:e?.name||String(e)}))]);
  out.home=home.error?home:{status:home.status,ct:home.ct,bytes:home.bytes,challenge:challenge(home.status,home.text)};
  out.rest=rest.error?rest:{status:rest.status,ct:rest.ct,bytes:rest.bytes};
  const fingerprintText=(home.text||"")+"\\n"+(rest.text||"");
  for(const p of ["woocommerce google product feed","product feed pro","adtribes","feedcraft","codesolz","wppfm","merchant feed booster","google listings & ads"]) if(new RegExp(p,"i").test(fingerprintText)) out.fingerprints.push(p);
  const derived=[];
  for(const body of [home.text||"",rest.text||""]) {
    for(const m of String(body).matchAll(/(?:(?:https?:)?\/\/|\/)[^"'<>\\s]+/g)) {
      const u=m[0].startsWith("/")?new URL(m[0],base+"/").href:m[0];
      if(sameOrigin(u,base) && /(google|merchant|shopping|feed|product|wppfm|woo-feed|codesolz|feedcraft)/i.test(u)) derived.push(u);
    }
  }
  const primary=PRIMARY.map(p=>new URL(p,base+"/").href);
  const derivedUnique=[...new Set(derived)];
  await probeList([...new Set([...primary,...derivedUnique])],out,true);
  if(!out.feed) {
    await probeList(PLUGIN.map(p=>new URL(p,base+"/").href),out,true);
  }
  if(!out.feed && home.status===200 && !challenge(home.status,home.text)) {
    await browserDiscover(base,out);
  }
  if(!out.feed && out.fingerprints.length) {
    await historyFallback(base,out);
  }
  return out;
}

const results = await Promise.all(SELECTED.map(t=>scan(t)));
const feeds = results.flatMap(r=>r.feed?[{brand:r.name,base:r.base,...r.feed}]:[]);
await writeFile("out/fast2/summary.json",JSON.stringify({
  generated_at:new Date().toISOString(),targets:SELECTED.length,live_verified_feeds:feeds.length,
  live_verified_sites:new Set(feeds.map(x=>x.brand)).size,
  sites:results.map(r=>({brand:r.name,feed:r.feed?.url||null,fingerprints:r.fingerprints,home:r.home,browser_hits:r.browser_hits.length,history_candidates:r.history_candidates.length}))
},null,2)+"\n");
await writeFile("out/fast2/audit.json",JSON.stringify({generated_at:new Date().toISOString(),targets:SELECTED.length,results,feeds},null,2)+"\n");
