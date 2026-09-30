#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";

const UA = "Mozilla/5.0 (compatible; WooCommerceKnownFeedGuessCalibration/2026.09)";
const TARGETS = [
  ["PC Studio","https://www.pcstudio.in"],
  ["Quickin Computers","https://quickincomputers.com"],
  ["Avikaretails","https://avikaretails.com"],
  ["Geekbees","https://geekbees.in"],
  ["Ninja Dog","https://ninjadog.in"],
  ["Network IT Store","https://networkitstore.in"],
  ["My Nexus Infosys","https://www.mynexusinfosys.com"],
  ["Solanki Enterprises","https://solankienterprises.com"],
  ["Only SSD","https://onlyssd.com"],
  ["IT Gadgets Online","https://itgadgetsonline.com"],
];
const FIXED = {
  woocommerce_google_product_feed: ["/?woocommerce_gpf=google","/woocommerce_gpf/google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100"],
  ctx_feed_webappick: ["/?woo_feed=google&wt=xml","/?woo_feed=google_shopping&wt=xml"],
  adtribes_product_feed_pro: ["/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml"],
  wpfm_product_feed_manager: ["/wp-content/uploads/wppfm-feeds/google.xml","/wp-content/uploads/wppfm-feeds/google-shopping.xml"],
  webtoffee_product_feed: ["/wp-content/uploads/webtoffee_product_feed/wt_Google_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml"],
  codesolz_merchant_feed_booster: ["/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-content/uploads/codesolz-feeds/google.xml"],
  feedcraft: ["/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/json"],
};
const DIRECTORIES = [
  ["/wp-content/uploads/woo-feed/google/xml/","ctx_feed_webappick"],
  ["/wp-content/uploads/woo-feed/google/","ctx_feed_webappick"],
  ["/wp-content/uploads/woo-product-feed-pro/xml/","adtribes_product_feed_pro"],
  ["/wp-content/uploads/wppfm-feeds/","wpfm_product_feed_manager"],
  ["/wp-content/uploads/webtoffee_product_feed/","webtoffee_product_feed"],
  ["/wp-content/uploads/codesolz-feeds/","codesolz_merchant_feed_booster"],
  ["/feeds/","generic_public_feed"], ["/feed/","generic_public_feed"],
];
function sameHost(a,b){try{return new URL(a).hostname.replace(/^www\\./,"").toLowerCase()===new URL(b).hostname.replace(/^www\\./,"").toLowerCase()}catch{return false}}
function valid(body,ct=""){const x=String(body||""), l=x.toLowerCase(); return (l.includes("http://base.google.com/ns/1.0")||l.includes("https://base.google.com/ns/1.0")) && (l.includes("<rss")||l.includes("<feed")) && (l.includes("<item")||l.includes("<entry")) && l.includes("<g:id") && l.includes("<g:title") && l.includes("<g:link") && l.includes("<g:price") && !/just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser/i.test(l) && (/xml|rss|atom/i.test(ct)||(l.includes("<rss")||l.includes("<feed")));}
async function get(url,ms=9000,accept="application/xml,text/xml,text/html,text/plain,*/*"){const c=new AbortController();const t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(url,{redirect:"follow",signal:c.signal,headers:{"User-Agent":UA,"Accept":accept,"Accept-Language":"en-IN,en;q=0.9"}});return {status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body:await r.text()}}catch(e){return {status:0,url,error:e?.name||String(e),body:""}}finally{clearTimeout(t)}}
function xmlLinks(text,base){const out=new Set();for(const m of String(text||"").matchAll(/(?:href|src|loc|data-href)=["']([^'"]+)["']/gi)){try{const u=new URL(m[1],base).href;if(sameHost(u,base)&&/\\.xml(?:\\.gz)?(?:$|[?#])/i.test(new URL(u).pathname))out.add(u)}catch{}}for(const m of String(text||"").matchAll(/https?:\\/\\/[^\\s"'<>]+/gi)){try{const u=m[0].replace(/[),.;]+$/,"");if(sameHost(u,base)&&/\\.xml(?:\\.gz)?(?:$|[?#])/i.test(new URL(u).pathname))out.add(u)}catch{}}return [...out].slice(0,80)}
async function probe(base,url,family,lane){const r=await get(url);return {lane,family,url,status:r.status,final_url:r.url||"",content_type:r.ct||"",native:valid(r.body,r.ct),same_host:sameHost(r.url||"",base)}}
async function fixedLane(base){const jobs=[];for(const [family,paths] of Object.entries(FIXED))for(const p of paths)jobs.push(probe(base,new URL(p,base).href,family,"fixed_paths"));return Promise.all(jobs)}
async function directoryLane(base){const jobs=DIRECTORIES.map(async ([dir,family])=>{const index=await get(new URL(dir,base).href,8000,"text/html,text/plain,*/*");if(index.status!==200)return [{lane:"directory_index",family,url:new URL(dir,base).href,status:index.status,final_url:index.url||"",content_type:index.ct||"",native:false,same_host:sameHost(index.url||"",base)}];return Promise.all(xmlLinks(index.body,index.url||new URL(dir,base).href).slice(0,30).map(u=>probe(base,u,family,"directory_index")))});return (await Promise.all(jobs)).flat()}
async function referenceLane(base){const pages=["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml"];const rs=await Promise.all(pages.map(p=>get(new URL(p,base).href,7000)));const urls=new Set();for(const r of rs)for(const u of xmlLinks(r.body,base))if(/feed|google|merchant|shopping|woo|wpfm|webtoffee|adtribes|product/i.test(u))urls.add(u);return Promise.all([...urls].slice(0,40).map(u=>probe(base,u,"public_reference","public_reference")))}
async function waybackLane(base){const host=new URL(base).hostname.replace(/^www\\./,"");const q=new URL("https://web.archive.org/cdx/search/cdx");q.searchParams.set("url",host+"/*");q.searchParams.set("output","json");q.searchParams.set("fl","original,statuscode,mimetype");q.searchParams.append("filter","statuscode:200");q.searchParams.append("filter","urlkey:.*(feed|google|merchant|shopping|woo_feed|woocommerce_gpf|wpfm|webtoffee|adtribes|product-feed).*");q.searchParams.set("collapse","urlkey");q.searchParams.set("limit","50");const r=await get(q.href,12000,"application/json,text/plain,*/*");if(r.status!==200)return [];let rows=[];try{rows=JSON.parse(r.body)}catch{return []}const urls=(Array.isArray(rows)&&Array.isArray(rows[0])?rows.slice(1).map(x=>x[0]):[]).filter(u=>sameHost(u,base)).slice(0,20);return Promise.all(urls.map(u=>probe(base,u,"historical_hint","wayback")))}
async function main(){const wanted=process.env.SITE;const target=TARGETS.find(x=>x[0]===wanted);if(!target)process.exit(2);const base=target[1],started=Date.now();const [fixed,directory,reference,wayback]=await Promise.all([fixedLane(base),directoryLane(base),referenceLane(base),waybackLane(base)]);const all=[...fixed,...directory,...reference,...wayback];const hits=all.filter(x=>x.native&&x.same_host);return {schema:"woocommerce-known-feed-guess-calibration/v1",site:wanted,base,known_target:true,active_cohort:false,methods:["fixed_paths","directory_index","public_reference","wayback"],elapsed_s:Number(((Date.now()-started)/1000).toFixed(2)),verified_guess_hits:hits,sampled_results:all.filter(x=>x.status===200||x.native).slice(0,120)}}
await mkdir("out/woocommerce-known-feed-guess-calibration",{recursive:true});const result=await main();const slug=result.site.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"");await writeFile("out/woocommerce-known-feed-guess-calibration/"+slug+".json",JSON.stringify(result,null,2),"utf8");console.log(JSON.stringify({site:result.site,hits:result.verified_guess_hits,families:[...new Set(result.verified_guess_hits.map(x=>x.family))],elapsed_s:result.elapsed_s}));