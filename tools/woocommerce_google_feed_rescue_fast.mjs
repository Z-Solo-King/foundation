import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const TARGETS = [
  ["Aarna Computers","https://aarnacomputers.com"],
  ["Ads Store","https://adsstore.in"],
  ["ithunt","https://ithunt.in"],
  ["kccomputers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["networkitstore","https://networkitstore.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Moskeys","https://moskeys.com"],
  ["Ninja Dog","https://ninjadog.in"],
  ["Theproaudio","https://www.theproaudio.com"],
  ["quickincomputers","https://quickincomputers.com"],
  ["Prime ABGB","https://www.primeabgb.com"],
  ["Viper PC","https://viperpc.in"]
];

const FEEDS = [
  "/?woocommerce_gpf=google","/woocommerce_gpf/google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
  "/google-products.xml","/google-product-feed.xml",
  "/google.xml","/google_feed.xml","/google_base.xml",
  "/google-shopping.xml","/google-shopping-feed.xml",
  "/product-feed.xml","/products-feed.xml","/merchant-feed.xml",
  "/feed/google.xml","/feed/google-products.xml","/feeds/google.xml",
  "/feeds/google-products.xml","/feeds/google-product-feed.xml",
  "/feeds/google-shopping.xml","/feed.xml","/rss.xml","/products.rss",
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-content/uploads/woo-feed/google/xml/google.xml",
  "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/wppfm-feeds/google.xml",
  "/wp-json/feedcraft-product-feed/v1/xml"
];

const UA = "Mozilla/5.0 (compatible; WooCommerceGoogleRescueFast/2.0)";
const ROOT = "out/rescue-fast";
const PAGE_SIZE = 100;
await mkdir(ROOT + "/feeds", {recursive:true});
await mkdir(ROOT + "/raw", {recursive:true});

const slug = s => String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,70) || "site";

function challenge(status,text="") {
  const x = String(text).slice(0,10000).toLowerCase();
  return [403,429,430,451,503,520,521,522,523,524].includes(status) &&
    /just a moment|cloudflare|challenge-platform|turnstile|captcha|access denied|request blocked|attention required|checking your browser/.test(x);
}
function xmlEscape(v) {
  return String(v ?? "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;");
}
function strip(v) { return String(v ?? "").replace(/<[^>]*>/g," ").replace(/\s+/g," ").trim(); }
function nativeValid(s) {
  const x = String(s || "");
  return /^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(x) &&
    /xmlns(?::[\w.-]+)?\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(x) &&
    /<item\b[\s\S]*?<title\b/i.test(x) && /<(?:[\w.-]+:)?price\b/i.test(x);
}
function backupItem(p,base) {
  const id = String(p?.id ?? p?.sku ?? "").trim();
  const sku = String(p?.sku || "").trim();
  const title = strip(p?.name || "");
  const link = String(p?.permalink || "").trim();
  const image = String(p?.images?.[0]?.src || "").trim();
  const priceObj = p?.prices || {};
  const rawPrice = Number(priceObj.price);
  if (!id || !title || !link || !image || !Number.isFinite(rawPrice)) return null;
  const minor = Number(priceObj.currency_minor_unit);
  const decimals = Number.isFinite(minor) ? minor : 2;
  const price = (rawPrice / Math.pow(10,decimals)).toFixed(decimals) + " " + String(priceObj.currency_code || "").toUpperCase();
  const host = new URL(base).hostname.replace(/[^A-Za-z0-9.-]/g,"-");
  return [
    "    <item>",
    "      <g:id>" + xmlEscape((host + "-" + (sku || id)).slice(0,70)) + "</g:id>",
    "      <title>" + xmlEscape(title.slice(0,150)) + "</title>",
    "      <link>" + xmlEscape(link) + "</link>",
    "      <description>" + xmlEscape(strip(p?.short_description || p?.description || title).slice(0,5000)) + "</description>",
    "      <g:image_link>" + xmlEscape(image) + "</g:image_link>",
    "      <g:price>" + xmlEscape(price.trim()) + "</g:price>",
    "      <g:availability>" + (p?.is_in_stock ? "in stock" : "out of stock") + "</g:availability>",
    "      <g:condition>new</g:condition>",
    sku ? "      <g:mpn>" + xmlEscape(sku.slice(0,70)) + "</g:mpn>" : "",
    "    </item>"
  ].filter(Boolean).join("\n");
}
async function get(url,timeout=7000) {
  const ac = new AbortController(), t = setTimeout(()=>ac.abort(),timeout);
  try {
    const r = await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
      "User-Agent":UA,
      "Accept":"application/json,application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2"
    }});
    const b = Buffer.from(await r.arrayBuffer());
    return {status:r.status,url:r.url,ct:r.headers.get("content-type") || "",headers:r.headers,buf:b,text:b.length<24*1024*1024?b.toString("utf8"):"",bytes:b.length};
  } finally { clearTimeout(t); }
}
async function curlJson(url, timeout=12000) {
  try {
    const args=["-sS","-L","-4","--connect-timeout","5","--max-time",String(Math.ceil(timeout/1000)),"-A",UA,"-H","Accept: application/json",url];
    const {stdout}=await execFileAsync("curl",args,{timeout:timeout+2000,maxBuffer:24*1024*1024});
    const text=String(stdout||"").trim();
    const data=JSON.parse(text);
    return Array.isArray(data)&&data.length?{data,via:"curl"}:null;
  } catch { return null; }
}
async function storeRace(base,out) {
  const cs=[
    new URL("/wp-json/wc/store/v1/products",base + "/"),
    new URL("/wp-json/wc/store/v1/products/",base + "/"),
    new URL("/?rest_route=/wc/store/v1/products",base + "/"),
    new URL("/index.php?rest_route=/wc/store/v1/products",base + "/")
  ];
  const rs=await Promise.all(cs.map(async e=>{
    const u=new URL(e.href); u.searchParams.set("page","1"); u.searchParams.set("per_page","3");
    try {
      const r=await get(u.href,7000); let data=null; try{data=JSON.parse(r.text);}catch{}
      return {endpoint:e.href,request:u.href,response:r,data,ok:r.status===200&&Array.isArray(data)&&data.length>0,source:"fetch"};
    } catch(err) { return {endpoint:e.href,request:u.href,error:err?.name||String(err),ok:false,source:"fetch"}; }
  }));
  out.store_api_candidates.push(...rs.map(x=>x.error?{url:x.request,error:x.error,via:x.source}:{url:x.request,status:x.response.status,bytes:x.response.bytes,ok:x.ok,challenge:challenge(x.response.status,x.response.text),via:x.source}));
  let winner=rs.find(x=>x.ok)||null;
  if(!winner){
    const cr=await Promise.all(cs.map(async e=>{
      const u=new URL(e.href); u.searchParams.set("page","1"); u.searchParams.set("per_page","3");
      const z=await curlJson(u.href);
      return z?{endpoint:e.href,request:u.href,data:z.data,ok:true,source:"curl"}:null;
    }));
    winner=cr.find(Boolean)||null;
    out.store_api_candidates.push(...cr.filter(Boolean).map(x=>({url:x.request,status:200,bytes:x.data.length,ok:true,via:x.source})));
  }
  return winner;
}
async function reconstruct(base,out,winner) {
  const endpoint=new URL(winner.endpoint), products=[], seen=new Set();
  let page=1, pageSize=100, stopped=false;
  const seed=Array.isArray(winner.data)?winner.data:[];
  while(!stopped && page<=250 && products.length<20000){
    let data=null, headers=null;
    const u=new URL(endpoint.href); u.searchParams.set("page",String(page)); u.searchParams.set("per_page",String(pageSize));
    u.searchParams.set("orderby","id"); u.searchParams.set("order","asc");
    try{
      const r=await get(u.href,9000);
      if(r.status===200){ try{data=JSON.parse(r.text);headers=r.headers;}catch{} }
    }catch{}
    if(!Array.isArray(data)||!data.length){
      if(page===1 && seed.length){ data=seed; pageSize=3; }
      else {
        const fu=new URL(endpoint.href); fu.searchParams.set("page",String(page)); fu.searchParams.set("per_page","3");
        fu.searchParams.set("orderby","id"); fu.searchParams.set("order","asc");
        const z=await curlJson(fu.href,12000);
        if(z){ data=z.data; pageSize=3; }
      }
    }
    if(!Array.isArray(data)||!data.length) break;
    for(const p of data){ const k=String(p?.id??p?.sku??""); if(k&&!seen.has(k)){seen.add(k);products.push(p);} }
    const totalPages=Number(headers?.get?.("x-wp-totalpages"))||0;
    const total=Number(headers?.get?.("x-wp-total"))||0;
    if((totalPages&&page>=totalPages)||(total&&page>=Math.ceil(total/pageSize))||(!totalPages&&!total&&data.length<pageSize)) stopped=true;
    page++;
  }
  out.store_api={endpoint:winner.request,pages_fetched:Math.max(0,page-1),total_products:products.length,page_size:pageSize,transport:winner.source||"fetch"};
  if(!products.length) return false;
  await writeFile(ROOT+"/raw/"+slug(out.name)+"-store-api.json",JSON.stringify(products));
  const items=products.map(p=>backupItem(p,base)).filter(Boolean);
  const xml=[
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0">',
    "  <channel>",
    "    <title>"+xmlEscape(new URL(base).hostname)+" WooCommerce Public Store API Backup</title>",
    "    <link>"+xmlEscape(base)+"</link>",
    "    <description>Public WooCommerce Store API snapshot converted to Google Merchant RSS format.</description>",
    ...items,"  </channel>","</rss>",""
  ].join("\n");
  const hash=createHash("sha256").update(xml).digest("hex");
  const file=ROOT+"/feeds/"+slug(out.name)+"-store-api-"+hash.slice(0,12)+".xml";
  await writeFile(file,xml);
  out.reconstructed_feed={source:"PUBLIC_WOOCOMMERCE_STORE_API_RECONSTRUCTION",url:winner.request,file,sha256:hash,bytes:Buffer.byteLength(xml),valid_items:items.length,skipped_products:products.length-items.length,note:"Backup snapshot; not the retailer's native Merchant Center feed URL."};
  return true;
}
async function nativeRace(base,out) {
  let idx=0, won=false;
  const worker=async()=>{ while(idx<FEEDS.length && !won) {
    const path=FEEDS[idx++], url=new URL(path,base + "/").href;
    try {
      const r=await get(url);
      const hit={url,status:r.status,bytes:r.bytes};
      if(r.status===200 && nativeValid(r.text)) {
        won=true;
        const hash=createHash("sha256").update(r.buf).digest("hex");
        const file=ROOT + "/feeds/" + slug(out.name) + "-native-" + hash.slice(0,12) + ".xml";
        await writeFile(file,r.buf);
        out.feed={url,finalUrl:r.url,source:"PUBLIC_NATIVE_FEED",file,sha256:hash,bytes:r.bytes};
        out.native_candidate=hit;
        break;
      }
      hit.classification=r.status===200?"NO_MATCH":challenge(r.status,r.text)?"BLOCKED_OR_CHALLENGED":r.status===429?"RATE_LIMITED":r.status===403?"ACCESS_DENIED":"HTTP_"+r.status;
      out.native_candidates.push(hit);
    } catch(err) { out.native_candidates.push({url,classification:err?.name==="AbortError"?"TIMEOUT":"ERROR",error:err?.name || String(err)}); }
  }};
  await Promise.all(Array.from({length:12},worker));
  return won;
}
async function scan([name,base]) {
  const out={name,base,feed:null,reconstructed_feed:null,store_api:null,store_api_candidates:[],native_candidates:[]};
  const winner=await storeRace(base,out);
  if(winner){
    await Promise.all([reconstruct(base,out,winner),nativeRace(base,out)]);
  }else{
    await nativeRace(base,out);
  }
  out.status=out.feed?"NATIVE_FEED_VERIFIED":out.reconstructed_feed?"PUBLIC_STORE_API_BACKUP":"NO_PUBLIC_FEED_OR_STORE_API";
  return out;
}
const started=Date.now();
const results=await Promise.all(TARGETS.map(scan));
const feeds=results.filter(x=>x.feed).map(x=>x.feed);
const reconstructed=results.filter(x=>x.reconstructed_feed).map(x=>x.reconstructed_feed);
const summary={
  generated_at:new Date().toISOString(),
  duration_ms:Date.now()-started,
  targets:results.length,
  native_verified_sites:feeds.length,
  reconstructed_backup_sites:reconstructed.length,
  reconstructed_backup_products:results.reduce((n,x)=>n+Number(x.store_api?.total_products||0),0),
  status_counts:Object.groupBy(results,x=>x.status),
  sites:results.map(x=>({brand:x.name,base:x.base,status:x.status,native_feed:x.feed?.url || null,reconstructed_file:x.reconstructed_feed?.file || null,products:x.store_api?.total_products || 0,pages:x.store_api?.pages_fetched || 0,store_api_candidates:x.store_api_candidates,native_candidates:x.native_candidates.slice(0,80)}))
};
await writeFile(ROOT + "/summary.json",JSON.stringify(summary,null,2) + "\n");
await writeFile(ROOT + "/audit.json",JSON.stringify({generated_at:new Date().toISOString(),results,feeds,reconstructed},null,2) + "\n");
console.log(JSON.stringify(summary,null,2));