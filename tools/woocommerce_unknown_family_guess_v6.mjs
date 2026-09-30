#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";

const TARGETS = [
  ["Aarna Computers","https://aarnacomputers.com"],
  ["Ads Store","https://adsstore.in"],
  ["EZPZ Solutions","https://www.ezpzsolutions.in"],
  ["GamesNComps","https://gamesncomps.com"],
  ["hotshiftpc","https://hotshiftpc.com"],
  ["ithunt","https://ithunt.in"],
  ["KC Computers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["Viper PC","https://viperpc.in"],
  ["Cosmic Byte","https://www.thecosmicbyte.com"],
  ["Meckeys","https://www.meckeys.com"],
  ["StacksKB","https://stackskb.com"],
  ["Theproaudio","https://www.theproaudio.com"],
  ["Variety Infotech","https://varietyinfotech.com"]
];

const UA = "Mozilla/5.0 (compatible; WooCommerceUnknownFamilyGuess/6.0)";
const TIMEOUT = 6000;
const CONCURRENCY = 24;
const MAX_CANDIDATES = 450;
const CHALLENGE = /just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const GOOGLE_NS = /https?:\/\/base\.google\.com\/ns\/1\.0/i;

const ROOT_NAMES = [
  "google.xml","google-feed.xml","google_feed.xml","google-products.xml","google-product-feed.xml",
  "google-shopping.xml","google-shopping-feed.xml","google-merchant.xml","google-merchant-feed.xml",
  "merchant.xml","merchant-feed.xml","merchant_feed.xml","gpf.xml","product-feed.xml","products-feed.xml",
  "feed_products.xml","feed.xml"
];

const FAMILIES = {
  woocommerce_google_product_feed: {
    label: "WooCommerce Google Product Feed",
    candidates: [
      "/?woocommerce_gpf=google","/woocommerce_gpf/google",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
      "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
      "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
      "/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
      "/?woocommerce_gpf=google&currency=INR",
      "/?woocommerce_gpf=google&pricecountry=IN"
    ]
  },
  ctx_feed_webappick: {
    dirs: ["/wp-content/uploads/woo-feed/","/wp-content/uploads/woo-feed/xml/","/wp-content/uploads/woo-feed/google/","/wp-content/uploads/woo-feed/google/xml/"],
    names: ["google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml","google-product-feed.xml","google_merchant.xml","google-merchant.xml","merchantcenter2.xml","listings07.xml","google_shopping_ctx_1.xml","google_shopping_ctx_1-3.xml","googleshoplb24a.xml","feed.xml"],
    query: ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase","products","product-feed","listings","listings07","merchantcenter2"]
  },
  adtribes_product_feed_pro: {
    dirs: ["/wp-content/uploads/woo-product-feed-pro/","/wp-content/uploads/woo-product-feed-pro/xml/"],
    names: ["google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml","google-product-feed.xml","Google.xml","feed.xml"]
  },
  wpfm_product_feed_manager: {
    dirs: ["/wp-content/uploads/wppfm-feeds/"],
    names: ["Google.xml","Google-Products.xml","Google-Products-New.xml","Google-Products-1.xml","Google_Products.xml","Google-Feed.xml","Google-Feed_1.xml","GoogleFeed.xml","Google-Shopping.xml","Google-Shopping-Feed.xml","googlefeed.xml","google-feed.xml","google-products-feed.xml","feed-google.xml","feed-google-shopping.xml","feed.xml"]
  },
  webtoffee_product_feed: {
    dirs: ["/wp-content/uploads/webtoffee_product_feed/"],
    names: ["wt_google_Feed.xml","wt_gs_Feed.xml","wt_gmc_Feed.xml","wt_google_feed.xml","wt_google_products_Feed.xml","wt_google_shopping_Feed.xml","wt_google_shopping_feed.xml","google.xml","google-shopping.xml","google-product-feed.xml","google-shopping-feed.xml","feed.xml"]
  },
  codesolz_merchant_feed_booster: {
    dirs: ["/wp-content/uploads/codesolz-feeds/"],
    names: ["google-products.xml","google.xml","google-shopping.xml","google-feed.xml","merchant.xml","feed.xml"]
  },
  feedcraft: {
    candidates: [
      "/wp-json/feedcraft-product-feed/v1/xml",
      "/wp-json/feedcraft-product-feed/v1/google.xml",
      "/wp-json/feedcraft-product-feed/v1/feed.xml",
      "/wp-json/feedcraft-product-feed/v1/google",
      "/wp-json/google-product-feed/v1/xml",
      "/wp-json/google-feed/v1/xml",
      "/wp-json/woo-feed/v1/google.xml"
    ]
  },
  rexfeed: {
    dirs: ["/wp-content/uploads/rex-feed/"],
    names: ["feed.xml","google.xml","google-shopping.xml","google-products.xml","google-product-feed.xml","google-shopping-feed.xml","merchant.xml","merchant-feed.xml"]
  },
  klpsoft: {
    dirs: ["/wp-content/uploads/klp-feeds-xml/"],
    names: ["google.xml","google-feed.xml","google-products.xml","google-product-feed.xml","google-shopping.xml","merchant.xml","feed.xml"]
  },
  icopydoc: {
    candidates: [
      "/wp-content/uploads/feed-xml-0.xml",
      "/wp-content/uploads/feed-xml.xml",
      "/wp-content/uploads/google-feed.xml",
      "/wp-content/uploads/google-products.xml",
      "/wp-content/uploads/google-shopping.xml"
    ]
  }
};

const GENERIC_PATHS = [
  ...ROOT_NAMES.map(n => "/" + n),
  ...ROOT_NAMES.map(n => "/feed/" + n),
  ...ROOT_NAMES.map(n => "/feeds/" + n),
  "/catalog/feed","/catalog/feed.xml","/catalog/google.xml","/media/feed/google.xml",
  "/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml",
  "/wp-content/uploads/google_product_feed.xml","/wp-content/uploads/google-shopping.xml"
];

function host(u){ try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return ""} }
function sameHost(a,b){ return host(a)!=="" && host(a)===host(b) }
function abs(root,raw){ try{const u=new URL(String(raw),root); if(!/^https?:$/.test(u.protocol)||!sameHost(u.href,root)) return null; u.hash=""; return u.href}catch{return null} }

function native(body){
  const x=String(body||"");
  if(!x.trim()) return {valid:false,reason:"empty"};
  if(CHALLENGE.test(x.slice(0,40000))) return {valid:false,reason:"challenge_or_access_denied"};
  if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x)) return {valid:false,reason:"sitemap"};
  if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x)) return {valid:false,reason:"not_xml"};
  if(!GOOGLE_NS.test(x)) return {valid:false,reason:"no_google_namespace"};
  const blocks=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
  if(!blocks.length) return {valid:false,reason:"no_item_or_entry"};
  let good=0;
  for(const b of blocks) if(["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))) good++;
  return {valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function get(url){
  const ac=new AbortController();
  const timer=setTimeout(()=>ac.abort(),TIMEOUT);
  try{
    const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
      "user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.8,*/*;q=0.1",
      "accept-language":"en-IN,en;q=0.9"
    }});
    let b=Buffer.from(await r.arrayBuffer());
    if(b[0]===31&&b[1]===139){try{b=gunzipSync(b)}catch{}}
    const body=b.toString("utf8").slice(0,16*1024*1024);
    return {status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,transport:r.ok?"public_http":"http_error",challenge:CHALLENGE.test(body.slice(0,40000))};
  }catch(e){
    return {status:0,final_url:url,content_type:"",body:"",transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false};
  }finally{clearTimeout(timer);}
}

function siteTokens(name,root){
  const hostToken=host(root).split(".")[0];
  const words=name.toLowerCase().replace(/[^a-z0-9]+/g," ").trim().split(/\s+/).slice(0,4);
  const toks=new Set([hostToken,words.join("-"),words.join(""),...words]);
  return [...toks].filter(Boolean);
}
function add(m,root,raw,rank,family,source){
  const u=abs(root,raw); if(!u) return;
  const prev=m.get(u); const row={url:u,rank,family,source};
  if(!prev||rank>prev.rank) m.set(u,row);
}

function buildCandidates(name,root){
  const m=new Map();
  for(const [family,def] of Object.entries(FAMILIES)){
    for(const raw of def.candidates||[]) add(m,root,raw,320,family,"family-query");
    for(const d of def.dirs||[]) for(const n of def.names||[]) add(m,root,d+n,250,family,"family-fixed");
    for(const q of def.query||[]){
      add(m,root,"/?woo_feed="+encodeURIComponent(q)+"&wt=xml",300,family,"ctx-query");
      add(m,root,"/?woo_feed="+encodeURIComponent(q),285,family,"ctx-query-no-format");
    }
    for(const t of siteTokens(name,root)){
      for(const suffix of ["google.xml","google-feed.xml","google-products.xml","google-product-feed.xml","google-shopping.xml","google-shopping-feed.xml","merchant-feed.xml","product-feed.xml","feed.xml"]){
        for(const d of def.dirs||[]) add(m,root,d+t+"-"+suffix,150,family,"identity-semantic");
        for(const d of def.dirs||[]) add(m,root,d+t+"_"+suffix.replaceAll("-","_"),145,family,"identity-semantic-underscore");
      }
    }
  }
  for(const p of GENERIC_PATHS) add(m,root,p,120,"generic","generic-path");
  return [...m.values()].sort((a,b)=>b.rank-a.rank||a.url.localeCompare(b.url)).slice(0,MAX_CANDIDATES);
}

async function probeSite(name,root){
  const candidates=buildCandidates(name,root);
  const results=[];
  for(let i=0;i<candidates.length;i+=CONCURRENCY){
    const batch=await Promise.all(candidates.slice(i,i+CONCURRENCY).map(async c=>{
      const r=await get(c.url);
      const v=r.status===200&&sameHost(r.final_url,root)?native(r.body):{valid:false,reason:"http_or_redirect"};
      return {...c,status:r.status,final_url:r.final_url,content_type:r.content_type,transport:r.transport,challenge:r.challenge,validation:v};
    }));
    results.push(...batch);
  }
  const hits=results.filter(x=>x.validation.valid&&sameHost(x.final_url,root));
  const limited=results.some(x=>x.status===403||x.status===429||x.transport==="timeout"||x.challenge);
  return {
    site:name,root,family:"unknown_woocommerce",candidate_count:candidates.length,
    candidate_hits:hits.slice(0,20),positive_urls:hits.map(x=>x.final_url),
    status:hits.length?"NATIVE_FEED_VERIFIED":limited?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED",
    response_summary:{
      http_200:results.filter(x=>x.status===200).length,
      http_403:results.filter(x=>x.status===403).length,
      http_404:results.filter(x=>x.status===404).length,
      http_429:results.filter(x=>x.status===429).length,
      timeouts:results.filter(x=>x.transport==="timeout").length,
      challenges:results.filter(x=>x.challenge).length
    },
    family_attempts:[...new Set(candidates.map(x=>x.family))],
    evidence_sample:results.filter(x=>x.status===200||x.validation.valid).slice(0,80)
  };
}

const shard=Number(process.env.SHARD||1);
const shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
const outDir="out/woocommerce-unknown-family-guess-v6";
await mkdir(outDir,{recursive:true});
const results=await Promise.all(selected.map(([name,root])=>probeSite(name,root)));
const payload={
  schema:"woocommerce-unknown-family-guess-v6/v1",
  phase:"true-unknown-cross-family-guessing",
  target_count:results.length,shard,shards,
  strategy:"bounded-cross-family-matrix-after-identified-family-gate",
  policy:{public_only:true,no_store_api:true,no_product_extraction:true,no_plugin_extraction:true,no_playwright:true,no_auth:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true,native_acceptance:"current_same_host_google_merchant_xml_payload"},
  families:Object.fromEntries(Object.entries(FAMILIES).map(([k,v])=>[k,{label:v.label||k}])),
  results
};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(payload,null,2)+"\n");
console.log(JSON.stringify({
  shard,target_count:results.length,
  native_verified:results.filter(x=>x.candidate_hits.length).length,
  transport_limited:results.filter(x=>x.status.endsWith("TRANSPORT_LIMITED")).length,
  clean_no_hit:results.filter(x=>x.status==="NO_NATIVE_FEED_VERIFIED").length,
  candidate_total:results.reduce((n,x)=>n+x.candidate_count,0),
  positive_urls:results.flatMap(x=>x.positive_urls)
},null,2));
