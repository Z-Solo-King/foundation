#!/usr/bin/env node
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import path from "node:path";

const FAMILY_PATTERNS = {
  woocommerce_google_product_feed: [
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    ...[100,250,500,1000,2500,5000].map(n=>`/?woocommerce_gpf=google&gpf_start=0&gpf_limit=${n}`),
    ...[100,250,1000,5000].map(n=>`/woocommerce_gpf/google?gpf_start=0&gpf_limit=${n}`),
  ],
  ctx_feed_webappick: [
    "/?woo_feed=google&wt=xml","/?woo_feed=google-shopping&wt=xml","/?woo_feed=google_shopping&wt=xml",
    "/?woo_feed=google-products&wt=xml","/?woo_feed=google_product_feed&wt=xml",
    "/?woo_feed=google-feed&wt=xml","/?woo_feed=google_feed&wt=xml",
    "/?woo_feed=google-merchant&wt=xml","/?woo_feed=google_merchant&wt=xml",
    "/?woo_feed=gmc&wt=xml","/?woo_feed=googlebase&wt=xml",
    "/?woo_feed=products&wt=xml","/?woo_feed=product-feed&wt=xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/feed.xml",
    "/wp-content/uploads/woo-feed/google.xml",
  ],
  adtribes_product_feed_pro: [
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google_products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/google.xml.gz",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml.gz",
  ],
  webtoffee_product_feed: [
    "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml.gz",
    "/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml.gz",
    "/wp-content/uploads/webtoffee_product_feed/google.xml",
    "/wp-content/uploads/webtoffee_product_feed/google-shopping.xml",
    "/wp-content/uploads/webtoffee_product_feed/google-product-feed.xml",
  ],
  wpfm_product_feed_manager: [
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/product-feed.xml",
    "/wp-content/uploads/wppfm-feeds/google-product-feed.xml",
  ],
  codesolz_feed: [
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-shopping.xml",
    "/wp-content/uploads/codesolz-feeds/google-product-feed.xml",
  ],
  feedcraft: [
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/google",
    "/wp-json/feedcraft-product-feed/v1/feed.xml",
  ],
};

const GENERIC_DIRS = [
  "/",
  "/wp-content/uploads/",
  "/wp-content/uploads/woo-feed/",
  "/wp-content/uploads/woo-feed/google/",
  "/wp-content/uploads/woo-feed/google/xml/",
  "/wp-content/uploads/woo-product-feed-pro/",
  "/wp-content/uploads/woo-product-feed-pro/xml/",
  "/wp-content/uploads/wppfm-feeds/",
  "/wp-content/uploads/codesolz-feeds/",
  "/wp-content/uploads/webtoffee_product_feed/",
];

const GENERIC_NAMES = [
  "google.xml","google_feed.xml","google-feed.xml","google-products.xml","google_product_feed.xml",
  "google-product-feed.xml","google-shopping.xml","google_shopping.xml","google-shopping-feed.xml",
  "google-shopping-products.xml","google-merchant.xml","google_merchant.xml","google-merchant-feed.xml",
  "googlemerchant.xml","googlemerchantcenter.xml","googleshopping.xml","gshopping.xml","gads_shopping.xml",
  "merchant.xml","merchant-feed.xml","merchant_feed.xml","merchantfeed.xml","product-feed.xml",
  "product_feed.xml","productfeed.xml","products-feed.xml","feed.xml","data-feed.xml","gmc.xml","gpf.xml"
];

const IDENTITY_SEEDS = [
  "googlemerchantcenter","googlemerchant","googleshopping","google-shopping",
  "googlefeed","google-feed","productfeed","product-feed","merchantfeed","merchant-feed",
];

const FAMILY_DIRS = {
  ctx_feed_webappick: ["/wp-content/uploads/woo-feed/google/xml/","/wp-content/uploads/woo-feed/google/"],
  adtribes_product_feed_pro: ["/wp-content/uploads/woo-product-feed-pro/xml/","/wp-content/uploads/woo-product-feed-pro/"],
  webtoffee_product_feed: ["/wp-content/uploads/webtoffee_product_feed/"],
  wpfm_product_feed_manager: ["/wp-content/uploads/wppfm-feeds/"],
  codesolz_feed: ["/wp-content/uploads/codesolz-feeds/"],
};

const CHALLENGE_MARKERS = [
  "just a moment","cf-chl-","cf-turnstile","turnstile","captcha","access denied",
  "attention required","checking your browser"
];

const UA = "Mozilla/5.0 (compatible; WooCommerceXmlGuess/1.0; +https://github.com/Z-Solo-King/foundation)";
const MAX_BODY = 12 * 1024 * 1024;

function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function sameOrigin(a,b){
  try {
    const ah=(new URL(a)).hostname.toLowerCase().replace(/^www\./,"");
    const bh=(new URL(b)).hostname.toLowerCase().replace(/^www\./,"");
    return ah===bh;
  } catch { return false; }
}

async function publicGet(url, timeoutMs=4000, attempts=3){
  let last={status:0,finalUrl:url,body:"",contentType:"",transport:"request_error",challenge:false};
  for(let attempt=1;attempt<=attempts;attempt++){
    const controller=new AbortController();
    const timer=setTimeout(()=>controller.abort(),timeoutMs);
    try{
      const r=await fetch(url,{method:"GET",redirect:"follow",headers:{
        "user-agent":UA,
        "accept":"application/xml,text/xml,application/rss+xml;q=0.9,*/*;q=0.1",
        "cache-control":"no-cache",
      },signal:controller.signal});
      const ab=Buffer.from(await r.arrayBuffer());
      let data=ab;
      let decompressed=false;
      if(ab.length>=2 && ab[0]===0x1f && ab[1]===0x8b){
        try { data=gunzipSync(ab); decompressed=true; }
        catch { last={status:r.status,finalUrl:r.url||url,body:"",contentType:"",transport:"invalid_gzip",challenge:false}; continue; }
      }
      const body=data.toString("utf8").slice(0,MAX_BODY);
      const headers={"retry-after":r.headers.get("retry-after")||"","content-type":r.headers.get("content-type")||""};
      const challenge=CHALLENGE_MARKERS.some(m=>body.slice(0,20000).toLowerCase().includes(m));
      last={status:r.status,finalUrl:r.url||url,body,contentType:headers["content-type"],transport:r.ok?"public_http":"http_error",challenge,decompressed};
      if(![429,502,503,504].includes(r.status)) return last;
      const ra=parseInt(headers["retry-after"],10);
      await sleep(Number.isFinite(ra)?Math.min(ra*1000,5000):attempt*750);
    } catch(e){
      last={status:0,finalUrl:url,body:"",contentType:"",transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false,error:String(e?.message||e)};
      await sleep(attempt*500);
    } finally { clearTimeout(timer); }
  }
  return last;
}

function strictValidate(body){
  const text=String(body||"");
  const low=text.toLowerCase();
  if(!text.trim()) return {valid:false,reason:"empty_body"};
  if(CHALLENGE_MARKERS.some(m=>low.slice(0,20000).includes(m))) return {valid:false,reason:"interstitial_or_access_denied"};
  if(/^\s*<(?:urlset|sitemapindex)\b/i.test(text)) return {valid:false,reason:"sitemap"};
  if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(text)) return {valid:false,reason:"not_xml_looking"};
  if(!/xmlns:g\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(text)) return {valid:false,reason:"no_google_namespace"};
  const blocks=[];
  for(const m of text.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)) blocks.push(m[1]);
  for(const m of text.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)) blocks.push(m[1]);
  let validItems=0;
  for(const b of blocks){
    const ok=["id","title","link","price"].every(f=>new RegExp("<g:"+f+"\\b[^>]*>","i").test(b));
    if(ok) validItems++;
  }
  return {valid:validItems>0,reason:validItems>0?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:validItems};
}

function normalizeIdentityTokens(site){
  const source=[...(site.identity_tokens||[])];
  const host=(new URL(site.selected_origin||site.configured_root)).hostname.replace(/^www\./i,"").split(".")[0];
  source.push(host,site.site);
  return [...new Set(source.flatMap(v=>String(v).toLowerCase().split(/[^a-z0-9]+/).filter(x=>x.length>=2&&x.length<=40)))].slice(0,20);
}

function addUnique(map, root, p, rank, source){
  try{
    const u=new URL(p,root);
    if(!/^https?:$/.test(u.protocol) || !sameOrigin(u.href,root)) return;
    u.hash="";
    if(u.href.length>600) return;
    const old=map.get(u.href);
    if(!old || rank>old.rank) map.set(u.href,{url:u.href,rank,source});
  }catch{}
}

function candidatesFor(site, group){
  const root=(site.selected_origin||site.configured_root).replace(/\/+$/,"");
  const map=new Map();
  const add=(p,r,s)=>addUnique(map,root,p,r,s);
  if(group==="google_for_woocommerce"){
    return [{url:root+"/?woocommerce_gpf=google",rank:5,source:"legacy-confirmation-only"}];
  }
  for(const p of FAMILY_PATTERNS[group]||[]) add(p,200,"documented-plugin-family");
  if(group==="ctx_feed_webappick"){
    const names=["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase","products","product-feed"];
    for(const name of names) add("/?woo_feed="+name+"&wt=xml",190,"documented-ctx-query");
    for(const name of names) add("/?feed="+name+"&wt=xml",145,"legacy-ctx-query-variant");
  }
  if(group==="webtoffee_product_feed"){
    for(const n of ["wt_google_Feed.xml","wt_gs_Feed.xml","wt_google_shopping_Feed.xml","wt_google_feed.xml","wt_google_shopping_feed.xml","google.xml","google-shopping.xml","google-product-feed.xml"])
      add("/wp-content/uploads/webtoffee_product_feed/"+n,185,"documented-webtoffee-family");
  }
  for(const dir of (FAMILY_DIRS[group]||[])){
    for(const n of GENERIC_NAMES) add(dir+n,130,"generic-name-in-plugin-family");
    for(const token of normalizeIdentityTokens(site)){
      for(const seed of IDENTITY_SEEDS){
        for(const sep of ["","-","_"]){
          add(dir+token+sep+seed+".xml",120,"identity-derived");
          add(dir+seed+sep+token+".xml",119,"identity-derived");
        }
      }
      add(dir+token+".xml",112,"identity-derived");
      add(dir+token+"-feed.xml",111,"identity-derived");
      add(dir+token+"-google.xml",110,"identity-derived");
      add(dir+token+"-shopping.xml",109,"identity-derived");
    }
  }
  if(group==="unknown_woocommerce"){
    for(const known of Object.keys(FAMILY_PATTERNS)){
      if(known==="google_for_woocommerce") continue;
      for(const p of FAMILY_PATTERNS[known]) add(p,105,"unknown-known-family-fallback");
    }
    for(const dir of GENERIC_DIRS){
      for(const n of GENERIC_NAMES) add(dir+n,70,"generic-xml-guess");
    }
    for(const name of ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase"])
      add("/?woo_feed="+name+"&wt=xml",90,"generic-ctx-query");
  }
  // Use only URL naming guesses. Never mine HTML, JS, XML, directories, or search indexes for feed URLs.
  const all=[...map.values()].sort((a,b)=>b.rank-a.rank || a.url.localeCompare(b.url));
  const limit=group==="unknown_woocommerce" ? 450 : 240;
  return all.slice(0,limit);
}

async function pool(items,n,fn){
  const out=new Array(items.length); let next=0;
  async function worker(){
    while(true){
      const i=next++; if(i>=items.length) return;
      out[i]=await fn(items[i],i);
    }
  }
  await Promise.all(Array.from({length:Math.max(1,n)},worker)); return out;
}

async function main(){
  const args=process.argv.slice(2);
  const idx=k=>args.indexOf(k);
  const group=args[idx("--group")+1];
  const input=args[idx("--input")+1] || "out/plugin-groups.json";
  const outDir=args[idx("--out")+1] || "out/group-guess";
  if(!group) throw new Error("missing --group");
  await mkdir(outDir,{recursive:true});
  const matrix=JSON.parse(await readFile(input,"utf8"));
  const sites=matrix.sites.filter(s=>s.primary_group===group);
  const results=await pool(sites,6,async site=>{
    const cands=candidatesFor(site,group);
    if(group==="google_for_woocommerce"){
      return {site:site.site,group,candidate_count:cands.length,candidate_hits:[],blocked_or_limited:0,status:"API_SYNC_LIKELY_NO_TRADITIONAL_XML_FEED"};
    }
    const fastCandidates=cands.slice(0,140);
    const fast=await pool(fastCandidates,12,async c=>{
      const r=await publicGet(c.url,2500,2);
      const v=strictValidate(r.body);
      return {rank:c.rank,url:c.url,source:c.source,status:r.status,final_url:r.finalUrl,transport:r.transport,challenge:r.challenge,validation:v};
    });
    const fastHits=fast.filter(x=>x.validation.valid);
    let checks=[...fast];
    if(!fastHits.length){
      const rescue=fast.filter(x=>x.transport==="timeout" || x.status===429 || x.status===503 || x.status===504)
        .sort((a,b)=>b.rank-a.rank)
        .slice(0,24);
      const rescueUrls=new Set(rescue.map(x=>x.url));
      const slow=await pool([...rescueUrls],6,async url=>{
        const r=await publicGet(url,12000,2);
        const v=strictValidate(r.body);
        const source=fast.find(x=>x.url===url)?.source || "slow-transport-rescue";
        return {rank:fast.find(x=>x.url===url)?.rank||0,url,source,status:r.status,final_url:r.finalUrl,transport:r.transport,challenge:r.challenge,validation:v};
      });
      checks=checks.concat(slow);
    }
    const remaining=cands.slice(140);
    if(!checks.some(x=>x.validation.valid) && remaining.length){
      const second=await pool(remaining,12,async c=>{
        const r=await publicGet(c.url,2500,1);
        const v=strictValidate(r.body);
        return {rank:c.rank,url:c.url,source:c.source,status:r.status,final_url:r.finalUrl,transport:r.transport,challenge:r.challenge,validation:v};
      });
      checks=checks.concat(second);
    }
    const hits=checks.filter(x=>x.validation.valid && x.final_url && sameOrigin(x.final_url,site.configured_root));
    const limited=checks.filter(x=>x.transport==="timeout"||x.status===429||x.status===403||x.challenge);
    return {
      site:site.site,group,candidate_count:cands.length,
      candidate_hits:hits.slice(0,10),
      blocked_or_limited:limited.length,
      status:hits.length?"NATIVE_FEED_VERIFIED":limited.length?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED",
      transport_summary:{
        status_403:checks.filter(x=>x.status===403).length,
        status_429:checks.filter(x=>x.status===429).length,
        timeouts:checks.filter(x=>x.transport==="timeout").length,
        challenges:checks.filter(x=>x.challenge).length,
      }
    };
  });
  const summary={
    schema_version:"woocommerce-31-group-xml-guess/v1",
    generated_at:new Date().toISOString(),
    group,site_count:sites.length,
    policy:"Plugin-group URL guessing only. Public GETs, bounded retries, same-origin redirect enforcement. No Store API, product reconstruction, CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication or stealth/evasion.",
    results
  };
  await writeFile(path.join(outDir,"group-result.json"),JSON.stringify(summary,null,2)+"\n");
  const lines=["# XML Guess Result — "+group,"",`Sites: ${sites.length}`,"","| Site | Candidates | Native feed | Status | Limited transport signals |","|---|---:|---:|---|---:|"];
  for(const r of results) lines.push(`| ${r.site} | ${r.candidate_count} | ${r.candidate_hits.length?"YES":"NO"} | ${r.status} | ${r.blocked_or_limited} |`);
  await writeFile(path.join(outDir,"group-result.md"),lines.join("\n")+"\n");
  console.log(JSON.stringify({group,sites:sites.length,hits:results.filter(x=>x.candidate_hits.length).length,limited:results.reduce((n,x)=>n+(x.blocked_or_limited||0),0)},null,2));
}
await main();
