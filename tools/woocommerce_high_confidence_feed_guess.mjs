#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";

const TARGETS = [
  ["PC Studio","https://www.pcstudio.in","woocommerce_google_product_feed"],
  ["Quickin Computers","https://quickincomputers.com","ctx_feed_webappick"],
  ["Avikaretails","https://avikaretails.com","adtribes_product_feed_pro"],
  ["IT Gadgets Online","https://itgadgetsonline.com","wpfm_product_feed_manager"],
];

const FAMILY = {
  woocommerce_google_product_feed: {
    directories: [],
    fixed: [
      "/?woocommerce_gpf=google",
      "/woocommerce_gpf/google",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
      "/?woocommerce_gpf=google&gpf_start=100&gpf_limit=100",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
      "/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
    ],
    names: []
  },
  ctx_feed_webappick: {
    directories: [
      "/wp-content/uploads/woo-feed/xml/",
      "/wp-content/uploads/woo-feed/google/xml/",
      "/wp-content/uploads/woo-feed/google/",
      "/wp-content/uploads/woo-feed/"
    ],
    fixed: [
      "/?woo_feed=google&wt=xml",
      "/?woo_feed=google_shopping&wt=xml",
      "/?woo_feed=google-shopping&wt=xml",
      "/?woo_feed=google_merchant&wt=xml",
      "/wp-content/uploads/woo-feed/xml/google-shopping.xml",
      "/wp-content/uploads/woo-feed/xml/google.xml",
      "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
      "/wp-content/uploads/woo-feed/google/xml/google.xml",
      "/wp-content/uploads/woo-feed/google-shopping.xml"
    ],
    names: [
      "google-shopping.xml","google.xml","google-shopping-feed.xml","google-shopping-products.xml",
      "google_merchant.xml","google-merchant.xml","gshopping.xml","googleshopping.xml"
    ]
  },
  adtribes_product_feed_pro: {
    directories: [
      "/wp-content/uploads/woo-product-feed-pro/xml/",
      "/wp-content/uploads/woo-product-feed-pro/"
    ],
    fixed: [
      "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
      "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
      "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
      "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
      "/wp-content/uploads/woo-product-feed-pro/google.xml"
    ],
    names: [
      "google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml",
      "googleshopping.xml","googlefeed.xml"
    ]
  },
  wpfm_product_feed_manager: {
    directories: ["/wp-content/uploads/wppfm-feeds/"],
    fixed: [
      "/wp-content/uploads/wppfm-feeds/google.xml",
      "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
      "/wp-content/uploads/wppfm-feeds/google-feed.xml",
      "/wp-content/uploads/wppfm-feeds/google_products.xml",
      "/wp-content/uploads/wppfm-feeds/google-shopping-feed.xml"
    ],
    names: [
      "google.xml","google-shopping.xml","google-feed.xml","google_products.xml","google-shopping-feed.xml"
    ]
  }
};

const GENERIC = [
  "/google.xml","/google_feed.xml","/google-feed.xml","/google-products.xml","/google-product-feed.xml",
  "/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml",
  "/merchant.xml","/merchant-feed.xml","/product-feed.xml","/feed/google.xml","/feeds/google.xml",
  "/feed.xml"
];

const UA = "Mozilla/5.0 (compatible; WooCommerceHighConfidenceFeedGuess/2026.09)";
const CHALLENGE = /just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser/i;

function sameHost(a,b) {
  try { return new URL(a).hostname.toLowerCase().replace(/^www\./,"") === new URL(b).hostname.toLowerCase().replace(/^www\./,""); }
  catch { return false; }
}
function absolute(raw,base) {
  try {
    const u=new URL(String(raw||"").trim(),base);
    if (!["http:","https:"].includes(u.protocol) || !sameHost(u.href,base)) return null;
    u.hash="";
    return u.href;
  } catch { return null; }
}
function feedLike(u) {
  return /\.xml(?:\.gz)?(?:[?#].*)?$/i.test(u) || /feed|merchant|shopping|woocommerce_gpf|woo_feed|gpf|wppfm|webappick|adtribes/i.test(u);
}
function links(text,base) {
  const out=new Set(), s=String(text||"");
  for (const m of s.matchAll(/(?:href|src|data-href|data-url|url|feedUrl|feed_url|product_feed|google_feed)\s*[:=]\s*["']([^"']+)["']/gi)) {
    const u=absolute(m[1],base); if (u && feedLike(u)) out.add(u);
  }
  for (const m of s.matchAll(/https?:\/\/[^\s<>"']+/gi)) {
    const u=absolute(m[0].replace(/[),.;]+$/,""),base); if (u && feedLike(u)) out.add(u);
  }
  for (const m of s.matchAll(/<loc[^>]*>\s*([^<]+?)\s*<\/loc>/gi)) {
    const u=absolute(m[1],base); if (u && feedLike(u)) out.add(u);
  }
  for (const m of s.matchAll(/(?:[?&])woo_feed=([^&#"'\s]+)/gi)) {
    const u=absolute("/?woo_feed="+encodeURIComponent(m[1])+"&wt=xml",base); if (u) out.add(u);
  }
  return [...out];
}
function validate(body) {
  const x=String(body||""), h=x.slice(0,24000);
  if (!x.trim()) return {valid:false,reason:"empty"};
  if (CHALLENGE.test(h)) return {valid:false,reason:"interstitial_or_access_denied"};
  if (/^\s*<(?:urlset|sitemapindex)\b/i.test(x)) return {valid:false,reason:"sitemap"};
  if (!/<(?:\?xml\b|rss\b|feed\b|channel\b)/i.test(x.slice(0,1800))) return {valid:false,reason:"not_xml"};
  if (!/xmlns:g\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(x)) return {valid:false,reason:"no_google_namespace"};
  const blocks=[
    ...[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].map(m=>m[1]),
    ...[...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1])
  ];
  let validItems=0;
  for (const b of blocks) {
    if (["id","title","link","price"].every(f=>new RegExp("<g:"+f+"\\b[^>]*>\\s*[^<]+\\s*</g:"+f+">","i").test(b))) validItems++;
  }
  return {valid:validItems>0,reason:validItems?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:validItems};
}
async function get(url,ms=10000,retry=0) {
  const c=new AbortController(), t=setTimeout(()=>c.abort(),ms);
  try {
    const r=await fetch(url,{redirect:"follow",signal:c.signal,headers:{
      "User-Agent":UA,
      "Accept":"application/xml,application/rss+xml,text/xml,text/html,application/json;q=0.9,*/*;q=0.1",
      "Accept-Language":"en-IN,en;q=0.9"
    }});
    let buf=Buffer.from(await r.arrayBuffer());
    if (buf.length>=2 && buf[0]===0x1f && buf[1]===0x8b) { try { buf=gunzipSync(buf); } catch {} }
    if ((r.status===429 || r.status===430) && retry<1) {
      const wait=Number(r.headers.get("retry-after")||"");
      await new Promise(resolve=>setTimeout(resolve,Number.isFinite(wait)&&wait>=0?Math.min(30000,wait*1000):3000));
      return get(url,ms,retry+1);
    }
    return {status:r.status,url:r.url||url,contentType:r.headers.get("content-type")||"",body:buf.toString("utf8").slice(0,12*1024*1024),bytes:buf.length};
  } catch (e) {
    return {status:0,url,error:e?.name||String(e),body:"",bytes:0};
  } finally { clearTimeout(t); }
}
async function directory(base,dir) {
  const u=new URL(dir,base).href, r=await get(u,8000);
  if (r.status!==200) return {directory:dir,status:r.status,candidates:[]};
  const cs=links(r.body,r.url||u).filter(x=>/\.(?:xml|xml\.gz)$/i.test(new URL(x).pathname)).slice(0,120);
  return {directory:dir,status:r.status,candidates:[...new Set(cs)]};
}
function learningRecord(candidate, source, rank, response, validation) {
  return {rank,url:candidate,source,status:response.status,bytes:response.bytes,content_type:response.contentType||"",transport:response.error||"http",validation};
}
async function runSite([name,base,family]) {
  const spec=FAMILY[family];
  const started=Date.now();
  const discoveries=[];
  const pages=["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/wp-json/"];
  const pageResults=await Promise.all(pages.map(async p=>({path:p,response:await get(new URL(p,base).href,9000)})));
  const discovered=new Set();
  for(const p of pageResults) for(const u of links(p.response.body,base)) discovered.add(u);

  const dirs=await Promise.all(spec.directories.map(d=>directory(base,d)));
  for(const d of dirs) for(const u of d.candidates) discovered.add(u);

  const ordered=[];
  for (const u of discovered) ordered.push([u,"public_reference",250]);
  for (const p of spec.fixed) ordered.push([new URL(p,base).href,"plugin_fixed",220]);
  for (const d of spec.directories) for (const n of spec.names) ordered.push([new URL(d+n,base).href,"plugin_filename_guess",170]);
  for (const p of GENERIC) ordered.push([new URL(p,base).href,"generic_guess",100]);

  const dedup=new Map();
  for(const [u,source,score] of ordered){
    if(!sameHost(u,base)) continue;
    const prev=dedup.get(u);
    if(!prev||score>prev.score) dedup.set(u,{url:u,source,score});
  }
  const candidates=[...dedup.values()].sort((a,b)=>b.score-a.score||a.url.localeCompare(b.url)).slice(0,180);

  const checked=[];
  let winner=null;
  let cursor=0;
  const workers=8;
  async function worker(){
    while(!winner){
      const i=cursor++;
      if(i>=candidates.length) return;
      const c=candidates[i];
      const response=await get(c.url,i<30?15000:9000);
      const validation=validate(response.body);
      const rec=learningRecord(c.url,c.source,i+1,response,validation);
      checked.push(rec);
      if(validation.valid){
        winner=rec;
      }
    }
  }
  await Promise.all(Array.from({length:Math.min(workers,candidates.length)},worker));
  checked.sort((a,b)=>a.rank-b.rank);

  return {
    site:name,base,family,
    elapsed_s:Number(((Date.now()-started)/1000).toFixed(2)),
    discovery_pages:pageResults.map(x=>({path:x.path,status:x.response.status,bytes:x.response.bytes})),
    public_directory_results:dirs,
    candidate_count:candidates.length,
    winner,
    status:winner?"NATIVE_FEED_VERIFIED":"NO_NATIVE_FEED_VERIFIED",
    learning:{
      candidate_sources:Object.fromEntries(["public_reference","plugin_fixed","plugin_filename_guess","generic_guess"].map(s=>[s,checked.filter(x=>x.source===s).length])),
      first_success_source:winner?.source||null,
      first_success_rank:winner?.rank||null,
      response_patterns:{
        success_200:checked.filter(x=>x.status===200).length,
        challenge:checked.filter(x=>x.validation.reason==="interstitial_or_access_denied").length,
        not_xml:checked.filter(x=>x.validation.reason==="not_xml").length,
        no_google_namespace:checked.filter(x=>x.validation.reason==="no_google_namespace").length,
        sitemap:checked.filter(x=>x.validation.reason==="sitemap").length,
        empty:checked.filter(x=>x.validation.reason==="empty").length
      }
    },
    checked:checked.slice(0,180)
  };
}

async function main(){
  const results=await Promise.all(TARGETS.map(runSite));
  const groups={};
  for(const [name, , family] of TARGETS)(groups[family]??=[]).push(name);
  const out={schema:"woocommerce-high-confidence-feed-guess/v1",generated_at:new Date().toISOString(),targets:TARGETS.map(x=>x[0]),group_counts:Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,v.length])),results};
  const dir="out/woocommerce-high-confidence-feed-guess";
  await mkdir(dir,{recursive:true});
  await writeFile(dir+"/phase1.json",JSON.stringify(out,null,2)+"\n","utf8");
  const md=[
    "# WooCommerce High-Confidence Feed Guess — Phase 1",
    "",
    "Targets: PC Studio, Quickin Computers, Avikaretails, IT Gadgets Online.",
    "",
    "| Site | Family | Candidates | Native feed | First source | Rank |",
    "|---|---|---:|---|---|---:|",
    ...results.map(r=>"| "+r.site+" | "+r.family+" | "+r.candidate_count+" | "+(r.winner?"YES":"NO")+" | "+(r.winner?.source||"")+" | "+(r.winner?.rank||"")+" |"),
    "",
    "## Learning",
    "",
    ...results.map(r=>"### "+r.site+"\n- "+JSON.stringify(r.learning))
  ].join("\n");
  await writeFile(dir+"/phase1.md",md+"\n","utf8");
  console.log(JSON.stringify(results.map(r=>({site:r.site,family:r.family,native:Boolean(r.winner),url:r.winner?.url||null,source:r.winner?.source||null,rank:r.winner?.rank||null,candidates:r.candidate_count})),null,2));
}
await main();
