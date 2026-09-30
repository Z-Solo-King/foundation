#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";

const TARGETS = [
 ["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
 ["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],["ithunt","https://ithunt.in"],
 ["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["Kryptronix Gaming","https://kryptronix.in"],
 ["NCL Computer","https://nclcomputer.com"],["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://www.pchubshop.com"],
 ["Prime ABGB","https://www.primeabgb.com"],["SCL Gaming","https://sclgaming.in"],["Variety Infotech","https://varietyinfotech.com"],
 ["Viper PC","https://viperpc.in"],["AULA India","https://aulaindia.com"],["Cosmic Byte","https://www.thecosmicbyte.com"],
 ["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],
 ["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],["Avikaretails","https://avikaretails.com"],
 ["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],["Network IT Store","https://www.networkitstore.in"],
 ["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],["IT Gadgets Online","https://itgadgetsonline.com"]
];
const EXCLUDED=new Set(["Moskeys","Only SDD"]);
const ACTIVE=TARGETS.filter(([n])=>!EXCLUDED.has(n));

const FAMILY={
 "PC Studio":"woocommerce_google_product_feed",
 "Quickin Computers":"ctx_feed_webappick",
 "Avikaretails":"adtribes_product_feed_pro",
 "Geekbees":"google_for_woocommerce",
 "Ninja Dog":"google_for_woocommerce",
 "Network IT Store":"google_for_woocommerce",
 "My Nexus Infosys":"google_for_woocommerce",
 "Solanki Enterprises":"google_for_woocommerce",
 "IT Gadgets Online":"wpfm_product_feed_manager",
 "AULA India":"google_for_woocommerce"
};

const PATHS={
 woocommerce_google_product_feed:[
  "/?woocommerce_gpf=google","/woocommerce_gpf/google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
  "/?woocommerce_gpf=google&gpf_start=100&gpf_limit=100"
 ],
 ctx_feed_webappick:[
  "/?woo_feed=google&wt=xml","/?woo_feed=google_shopping&wt=xml","/?woo_feed=Google_Shopping&wt=xml",
  "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google/xml/google.xml"
 ],
 adtribes_product_feed_pro:[
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml"
 ],
 wpfm_product_feed_manager:[
  "/wp-content/uploads/wppfm-feeds/google.xml","/wp-content/uploads/wppfm-feeds/google-shopping.xml"
 ],
 webtoffee_product_feed:[
  "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
  "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml.gz",
  "/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml",
  "/wp-content/uploads/webtoffee_product_feed/google.xml"
 ],
 codesolz_merchant_feed_booster:[
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-content/uploads/codesolz-feeds/google.xml"
 ],
 feedcraft:["/wp-json/feedcraft-product-feed/v1/xml"]
};

const FAMILY_DIRS={
 ctx_feed_webappick:["/wp-content/uploads/woo-feed/google/xml/","/wp-content/uploads/woo-feed/google/","/wp-content/uploads/woo-feed/xml/","/wp-content/uploads/woo-feed/"],
 adtribes_product_feed_pro:["/wp-content/uploads/woo-product-feed-pro/xml/","/wp-content/uploads/woo-product-feed-pro/"],
 wpfm_product_feed_manager:["/wp-content/uploads/wppfm-feeds/"],
 webtoffee_product_feed:["/wp-content/uploads/webtoffee_product_feed/"],
 codesolz_merchant_feed_booster:["/wp-content/uploads/codesolz-feeds/"],
 feedcraft:[]
};
const ALL_DIRS=[...new Set(Object.values(FAMILY_DIRS).flat().concat(["/feeds/","/feed/"]))];
const GENERIC=["/google.xml","/google_feed.xml","/google-feed.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml","/product-feed.xml","/feed/google.xml","/feeds/google.xml","/feed.xml","/products.xml"];
const UA="Mozilla/5.0 (compatible; WooCommerce30GroupedFeedGuess/2026.09)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser/i;

function sameHost(a,b){try{return new URL(a).hostname.toLowerCase().replace(/^www\./,"")===new URL(b).hostname.toLowerCase().replace(/^www\./,"")}catch{return false}}
function abs(raw,base){try{const u=new URL(String(raw||"").trim(),base);if(!sameHost(u.href,base)||!/^https?:$/.test(u.protocol))return null;u.hash="";return u.href}catch{return null}}
function feedLike(u){return /\.(?:xml|xml\.gz)(?:[?#].*)?$/i.test(u)||/feed|merchant|shopping|woocommerce_gpf|woo_feed|gpf/i.test(u)}
function extractLinks(text,base){
 const out=new Set(),s=String(text||"");
 for(const m of s.matchAll(/(?:href|src|data-href|data-url|url|feedUrl|feed_url|product_feed|google_feed)\s*[:=]\s*["']([^"']+)["']/gi)){const u=abs(m[1],base);if(u&&feedLike(u))out.add(u)}
 for(const m of s.matchAll(/https?:\/\/[^\s<>"']+/gi)){const u=abs(m[0].replace(/[),.;]+$/,""),base);if(u&&feedLike(u))out.add(u)}
 for(const m of s.matchAll(/<loc[^>]*>\s*([^<]+?)\s*<\/loc>/gi)){const u=abs(m[1],base);if(u&&feedLike(u))out.add(u)}
 for(const m of s.matchAll(/(?:[?&])woo_feed=([^&#"'\s]+)/gi)){const u=abs("/?woo_feed="+encodeURIComponent(m[1])+"&wt=xml",base);if(u)out.add(u)}
 return [...out];
}
function validate(body){
 const x=String(body||""),h=x.slice(0,24000);
 if(!x.trim())return{valid:false,reason:"empty"};
 if(CHALLENGE.test(h))return{valid:false,reason:"interstitial_or_access_denied"};
 if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return{valid:false,reason:"sitemap"};
 if(!/<(?:\?xml\b|rss\b|feed\b|channel\b)/i.test(x.slice(0,1800)))return{valid:false,reason:"not_xml"};
 if(!/xmlns:g\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(x))return{valid:false,reason:"no_google_namespace"};
 const items=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].map(m=>m[1]);
 const entries=[...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
 let good=0;
 for(const b of [...items,...entries])if(["id","title","link","price"].every(f=>new RegExp("<g:"+f+"\\b[^>]*>\\s*[^<]+\\s*</g:"+f+">","i").test(b)))good++;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:items.length+entries.length,valid_items:good};
}
async function get(url,ms=10000,retry=0){
 const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);
 try{
  const r=await fetch(url,{redirect:"follow",signal:c.signal,headers:{
   "User-Agent":UA,"Accept":"application/xml,application/rss+xml,text/xml,text/html,application/json;q=0.9,*/*;q=0.1","Accept-Language":"en-IN,en;q=0.9"
  }});
  let buf=Buffer.from(await r.arrayBuffer());
  if(buf.length>=2&&buf[0]===0x1f&&buf[1]===0x8b){try{buf=gunzipSync(buf)}catch{}}
  if((r.status===429||r.status===430)&&retry<1){const ra=Number(r.headers.get("retry-after")||"");await new Promise(x=>setTimeout(x,Number.isFinite(ra)&&ra>=0?Math.min(30000,ra*1000):3000));return get(url,ms,retry+1)}
  return{status:r.status,url:r.url||url,body:buf.toString("utf8").slice(0,12*1024*1024),bytes:buf.length};
 }catch(e){return{status:0,url,error:e?.name||String(e),body:"",bytes:0}}
 finally{clearTimeout(t)}
}
async function dirCandidates(base,dir){
 const u=new URL(dir,base).href,r=await get(u,8000);
 if(r.status!==200)return{url:u,status:r.status,candidates:[]};
 return{url:u,status:r.status,candidates:extractLinks(r.body,u).filter(x=>/\.xml(?:\.gz)?$/i.test(new URL(x).pathname)).slice(0,100)};
}
async function runTarget(name,base){
 const family=FAMILY[name]||"unknown_feed_generator";
 const pages=["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/wp-json/"];
 const pageResults=await Promise.all(pages.map(async p=>({path:p,r:await get(new URL(p,base).href,9000)})));
 const discovered=new Set();
 for(const x of pageResults)for(const u of extractLinks(x.r.body,base))discovered.add(u);

 const dirList=family==="unknown_feed_generator"
  ? ALL_DIRS
  : [...new Set([...(FAMILY_DIRS[family]||[]),"/feeds/","/feed/"])];
 const dirs=await Promise.all(dirList.map(d=>dirCandidates(base,d)));
 for(const d of dirs)for(const u of d.candidates)discovered.add(u);

 let candidates=[...discovered];
 if(family!=="google_for_woocommerce")candidates.push(...(PATHS[family]||[]).map(p=>new URL(p,base).href));
 if(family==="unknown_feed_generator"){
  for(const f of Object.keys(PATHS))for(const p of PATHS[f])candidates.push(new URL(p,base).href);
  candidates.push(...GENERIC.map(p=>new URL(p,base).href));
 }
 candidates=[...new Set(candidates)].filter(u=>sameHost(u,base)&&feedLike(u)).slice(0,120);

 const checked=[];const concurrency=Number(process.env.GUESS_CONCURRENCY||10);let cursor=0,won=false;
 async function worker(){
  while(!won){
   const i=cursor++;if(i>=candidates.length)return;
   const u=candidates[i],r1=await get(u,i<20?12000:8000);
   let r=r1;if(r1.status===0&&r1.error==="AbortError"&&i<40)r=await get(u,45000);
   const v=validate(r.body);
   checked.push({rank:i+1,url:u,status:r.status,final_url:r.url||u,bytes:r.bytes,transport:r.error||"http",validation:v});
   if(v.valid)won=true;
  }
 }
 await Promise.all(Array.from({length:Math.min(concurrency,candidates.length)},worker));
 checked.sort((a,b)=>a.rank-b.rank);
 const native=checked.find(x=>x.validation.valid)||null;
 return{
  site:name,base,family,known_family:Boolean(FAMILY[name]),candidate_count:candidates.length,
  native_feed:native,
  blocked_or_interstitial:checked.filter(x=>x.status===403||x.validation.reason==="interstitial_or_access_denied"||x.transport==="AbortError").length,
  directories:dirs,
  status:native?"NATIVE_FEED_VERIFIED":family==="google_for_woocommerce"?"API_SYNC_NO_STANDALONE_XML_REFERENCE":"NO_NATIVE_FEED_VERIFIED"
 };
}
async function main(){
 const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
 const selected=ACTIVE.filter((_,i)=>i%shards===shard-1),results=[];
 for(const t of selected){const r=await runTarget(t[0],t[1]);results.push(r);console.log(JSON.stringify({site:r.site,family:r.family,candidates:r.candidate_count,native:Boolean(r.native_feed),status:r.status}))}
 const groups={};for(const [name] of ACTIVE)(groups[FAMILY[name]||"unknown_feed_generator"]??=[]).push(name);
 const out={schema:"woocommerce-30-grouped-feed-guess/v1",generated_at:new Date().toISOString(),shard,shards,active_targets:ACTIVE.length,group_counts:Object.fromEntries(Object.entries(groups).map(([k,v])=>[k,v.length])),results};
 const dir="out/woocommerce-30-grouped-feed-guess";await mkdir(dir,{recursive:true});await writeFile(dir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\n","utf8");
}
await main();
