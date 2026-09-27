#!/usr/bin/env node
import fs from "node:fs/promises";
import { chromium } from "playwright";

const NAV_TIMEOUT = 12000;
const SETTLE_MS = 1800;
const MAX_PAGES = 4;
const MAX_LINKS_PER_PAGE = 20;
const MAX_RESPONSES = 300;
const SITE_TIMEOUT = 60000;
const TARGETS = [
  ["ithunt","https://ithunt.in"],
  ["kccomputers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Moskeys","https://moskeys.com"],
  ["Theproaudio","https://www.theproaudio.com"]
];

function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function isPublicLink(u,root){
  try{
    const x=new URL(u,root), r=new URL(root);
    return /^https?:$/.test(x.protocol) &&
      x.hostname.replace(/^www\./,"")===r.hostname.replace(/^www\./,"") &&
      !/[#]$/.test(x.href) &&
      !/\/wp-(?:admin|login)|\/cart(?:\/|$)|\/checkout(?:\/|$)|\/my-account(?:\/|$)/i.test(x.pathname);
  }catch{return false}
}
function rank(u){
  const p=new URL(u).pathname.toLowerCase();
  let s=0;
  if(/\/product\//.test(p)) s+=10;
  if(/\/products?\//.test(p)) s+=9;
  if(/\/category\//.test(p)||/\/product-category\//.test(p)) s+=8;
  if(/\/shop\/?$/.test(p)) s+=6;
  if(/\/collections?\//.test(p)||/\/catalog\//.test(p)) s+=5;
  return s;
}
function xmlValid(status,ct,body){
  if(status!==200||!body||!/(?:xml|rss|atom)/i.test(ct+body.slice(0,200))) return null;
  if(!/base\.google\.com\/ns\/1\.0/i.test(body)||!/<(?:item|entry)\b/i.test(body)||!/(?:<g:)?(?:id|title|price|availability|condition)\b/i.test(body)) return null;
  const count=(body.match(/<(?:item|entry)\b/g)||[]).length;
  return count?{status,content_type:ct,bytes:Buffer.byteLength(body),item_count_observed:count,validation:"strict_google_merchant_xml"}:null;
}
async function probeSite(browser,[name,root]){
  const deadline = Date.now() + SITE_TIMEOUT;
  const ctx=await browser.newContext({userAgent:"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"});
  const page=await ctx.newPage();
  const queue=[root], seen=new Set(), pages=[], network=[], verified=[], api=[];
  const onResponse=async response=>{
    if(network.length>=MAX_RESPONSES)return;
    const ct=response.headers()["content-type"]||"", u=response.url(), status=response.status();
    network.push({url:u,status,content_type:ct,resource_type:response.request().resourceType()});
    if(status===200 && (/xml|rss|atom/i.test(ct) || /google|merchant|feed|shopping/i.test(u))){
      try{const body=await response.text(); const v=xmlValid(status,ct,body); if(v)verified.push({url:u,...v});}catch{}
    }
    if(status===200 && /json/i.test(ct)) api.push({url:u,status,content_type:ct,resource_type:response.request().resourceType()});
  };
  page.on("response",onResponse);
  for(let n=0;n<MAX_PAGES && queue.length && Date.now()<deadline;n++){
    const u=queue.shift(); if(seen.has(u)) continue; seen.add(u);
    try{
      const resp=await page.goto(u,{waitUntil:"domcontentloaded",timeout:NAV_TIMEOUT});
      await sleep(Math.min(SETTLE_MS, Math.max(0, deadline-Date.now())));
      const html=await page.content();
      const platform=/woocommerce|wc-ajax|\/wp-json\/wc/i.test(html)?"woocommerce":/__NEXT_DATA__|_next\/data/i.test(html)?"nextjs":/shopify/i.test(html)?"shopify":null;
      pages.push({requested_url:u,final_url:page.url(),status:resp?.status()??null,content_type:resp?.headers()?.["content-type"]||"",platform});
      const links=await page.locator("a[href]").evaluateAll(as=>as.map(a=>a.href).filter(Boolean));
      const candidates=links.filter(h=>isPublicLink(h,root)).sort((a,b)=>rank(b)-rank(a)).slice(0,MAX_LINKS_PER_PAGE);
      for(const h of candidates) if(!seen.has(h) && rank(h)>0) queue.push(h);
    }catch(e){pages.push({requested_url:u,status:null,error:e?.name||String(e)});}
  }
  await ctx.close();
  return {name,root,pages,verified_google_xml:[...new Map(verified.map(x=>[x.url,x])).values()],public_json_requests:[...new Map(api.map(x=>[x.url,x])).values()],network_requests:network,visited_pages:[...seen]};
}
async function main(){
  await fs.mkdir("out/feed-crawl-1247",{recursive:true});
  const browser=await chromium.launch({headless:true});
  try{
    const results=[]; for(const t of TARGETS) results.push(await probeSite(browser,t));
    const verified=results.flatMap(x=>x.verified_google_xml.map(v=>({...v,site:x.name})));
    const report={schema_version:"foundation-woocommerce-google-feed-product-crawl/v1",issue:1247,generated_on:new Date().toISOString(),sites:results.length,verified_google_xml:verified,results};
    await fs.writeFile("out/feed-crawl-1247/report.json",JSON.stringify(report,null,2));
    console.log(JSON.stringify({issue:1247,sites:results.length,verified_feed_count:verified.length,visited:results.map(x=>({site:x.name,pages:x.visited_pages.length,json:x.public_json_requests.length}))},null,2));
  }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exit(1)});