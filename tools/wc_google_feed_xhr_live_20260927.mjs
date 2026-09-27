#!/usr/bin/env node
import fs from "node:fs/promises";
import { chromium } from "playwright";

const SITE_TIMEOUT = 65000;
const NAV_TIMEOUT = 20000;
const SETTLE_MS = 7000;
const MAX_PAGES = 4;
const MAX_LINKS_PER_PAGE = 16;
const MAX_RESPONSES = 500;
const XHR_TIMEOUT = 60000;
const CONCURRENCY = 4;

const TARGETS = [
 ["Aarna Computers","https://aarnacomputers.com"],
 ["Ads Store","https://adsstore.in"],
 ["avikaretails","https://avikaretails.com"],
 ["EZPZ Solutions","https://www.ezpzsolutions.in"],
 ["GamesNComps","https://gamesncomps.com"],
 ["Geekbees","https://geekbees.in"],
 ["hotshiftpc","https://hotshiftpc.com"],
 ["itgadgetsonline","https://itgadgetsonline.com"],
 ["ithunt","https://ithunt.in"],
 ["kccomputers","https://kccomputers.co.in"],
 ["KRG KART","https://krgkart.com"],
 ["Kryptronix Gaming","https://kryptronix.in"],
 ["NCL Computer","https://nclcomputer.com"],
 ["networkitstore","https://networkitstore.in"],
 ["nexusinfosys","https://www.mynexusinfosys.com"],
 ["Only SDD","https://onlyssd.com"],
 ["PC Kumar Infotech","https://pckumar.in"],
 ["PC Studio","https://www.pcstudio.in"],
 ["PCHubShop","https://www.pchubshop.com"],
 ["Prime ABGB","https://www.primeabgb.com"],
 ["quickincomputers","https://quickincomputers.com"],
 ["SCL Gaming","https://sclgaming.in"],
 ["solankienterprises","https://solankienterprises.com"],
 ["Variety Infotech","https://varietyinfotech.com"],
 ["Viper PC","https://viperpc.in"],
 ["AULA India","https://aulaindia.com"],
 ["Cosmic Byte","https://www.thecosmicbyte.com"],
 ["Meckeys","https://www.meckeys.com"],
 ["Moskeys","https://moskeys.com"],
 ["Ninja Dog","https://ninjadog.in"],
 ["Stackskb","https://stackskb.com"],
 ["Theproaudio","https://www.theproaudio.com"]
];

const CANDIDATE_PATHS = [
 "/?woocommerce_gpf=google",
 "/woocommerce_gpf/google",
 "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
 "/google-products.xml",
 "/google-product-feed.xml",
 "/google.xml",
 "/google_feed.xml",
 "/google_base.xml",
 "/google-shopping.xml",
 "/google-shopping-feed.xml",
 "/product-feed.xml",
 "/products-feed.xml",
 "/merchant-feed.xml",
 "/feed/google.xml",
 "/feed/google-products.xml",
 "/feeds/google.xml",
 "/feeds/google-products.xml",
 "/feeds/google-product-feed.xml",
 "/feeds/google-shopping.xml",
 "/feed.xml",
 "/rss.xml",
 "/products.rss",
 "/wp-content/uploads/codesolz-feeds/google-products.xml",
 "/wp-content/uploads/woo-feed/google/xml/google.xml",
 "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
 "/wp-content/uploads/wppfm-feeds/google.xml",
 "/wp-json/feedcraft-product-feed/v1/xml"
];

function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

function xmlValidate(status, contentType, body){
  if(status !== 200 || !body) return null;
  const head = body.slice(0,5000);
  if(!/(?:xml|rss|atom)/i.test(contentType + head)) return null;
  if(!/base\\.google\\.com\\/ns\\/1\\.0/i.test(body)) return null;
  if(!/<(?:item|entry)\\b/i.test(body)) return null;
  if(!/(?:<(?:[\\w.-]+:)?(?:id|title|price|availability|condition)\\b)/i.test(body)) return null;
  const itemCount = (body.match(/<(?:item|entry)\\b/gi)||[]).length;
  return {
    validation:"strict_google_merchant_xml",
    status,
    content_type:contentType,
    bytes:Buffer.byteLength(body),
    item_count_observed:itemCount
  };
}

function likelyFeedUrl(u){
  return /google|merchant|shopping|feed|rss|xml/i.test(u);
}

function sameOrigin(u, root){
  try{
    const a=new URL(u,root), b=new URL(root);
    return /^https?:$/.test(a.protocol) && a.hostname===b.hostname;
  }catch{return false;}
}

function rank(u){
  try{
    const p=new URL(u).pathname.toLowerCase();
    if(/google|merchant|feed|shopping|rss|xml/.test(p)) return 10;
    if(/product/.test(p)) return 8;
    if(/category|shop/.test(p)) return 6;
    return 0;
  }catch{return 0;}
}

async function xhrProbe(page, urls, deadline){
  const remain = Math.max(1000, deadline-Date.now());
  return await page.evaluate(async ({urls, timeout})=>{
    function one(url){
      return new Promise(resolve=>{
        const xhr = new XMLHttpRequest();
        let done=false;
        const finish = (x)=>{ if(done)return; done=true; resolve(x); };
        const t=setTimeout(()=>finish({url,ok:false,error:"timeout"}), timeout);
        try{
          xhr.open("GET", url, true);
          xhr.setRequestHeader("Accept","application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2");
          xhr.onload=()=>{ clearTimeout(t); finish({
            url: xhr.responseURL || url,
            ok:true,
            status:xhr.status,
            content_type:xhr.getResponseHeader("content-type") || "",
            body: typeof xhr.responseText==="string" ? xhr.responseText : ""
          }); };
          xhr.onerror=()=>{ clearTimeout(t); finish({url,ok:false,error:"network"}); };
          xhr.ontimeout=()=>{ clearTimeout(t); finish({url,ok:false,error:"timeout"}); };
          xhr.send();
        }catch(e){ clearTimeout(t); finish({url,ok:false,error:String(e)}); }
      });
    }
    const out=[];
    for(let i=0;i<urls.length;i+=6){
      const batch=urls.slice(i,i+6);
      out.push(...await Promise.all(batch.map(one)));
    }
    return out;
  }, {urls, timeout:Math.min(XHR_TIMEOUT, remain-500)}).catch(e=>[{ok:false,error:String(e)}]);
}

async function probeSite(browser,[name,root]){
  const deadline=Date.now()+SITE_TIMEOUT;
  const ctx=await browser.newContext({
    userAgent:"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153 Safari/537.36",
    ignoreHTTPSErrors:true
  });
  const page=await ctx.newPage();
  const pages=[], network=[], verified=[], xhrResults=[], sourceHints=new Set();
  const responseTasks=[];

  page.on("response", response=>{
    if(network.length>=MAX_RESPONSES) return;
    const request=response.request();
    const ct=response.headers()["content-type"]||"";
    const u=response.url();
    const type=request.resourceType();
    network.push({url:u,status:response.status(),content_type:ct,resource_type:type});
    if(type==="xhr" || type==="fetch" || likelyFeedUrl(u)){
      responseTasks.push((async()=>{
        if(Date.now()>=deadline || response.status()!==200) return;
        if(!/(?:xml|rss|atom)/i.test(ct) && !likelyFeedUrl(u)) return;
        try{
          const body=await response.text();
          const v=xmlValidate(response.status(),ct,body);
          if(v) verified.push({site:name,discovery:"xhr/fetch-response",url:u,...v,body});
        }catch{}
      })());
    }
  });

  const queue=[root];
  const seen=new Set();
  while(queue.length && seen.size<MAX_PAGES && Date.now()<deadline){
    const u=queue.shift();
    if(seen.has(u)) continue;
    seen.add(u);
    try{
      const resp=await page.goto(u,{waitUntil:"domcontentloaded",timeout:NAV_TIMEOUT});
      await sleep(Math.min(SETTLE_MS, Math.max(0,deadline-Date.now())));
      const html=await page.content();
      for(const m of html.matchAll(/(?:https?:\\/\\/[^"'\\s<>]+|\\/(?:[^"'\\s<>]*?(?:google|merchant|feed|shopping|rss|xml)[^"'\\s<>]*))/gi)){
        if(m[0]) sourceHints.add(m[0].slice(0,1000));
      }
      pages.push({
        requested_url:u,
        final_url:page.url(),
        status:resp?.status()??null,
        content_type:resp?.headers()?.["content-type"]||"",
        title:await page.title().catch(()=>null)
      });
      await page.evaluate(()=>window.scrollTo(0,document.body.scrollHeight)).catch(()=>{});
      await sleep(Math.min(1800,Math.max(0,deadline-Date.now())));
      const links=await page.locator("a[href]").evaluateAll(as=>as.map(a=>a.href).filter(Boolean));
      const candidates=links.filter(h=>sameOrigin(h,root)).sort((a,b)=>rank(b)-rank(a)).slice(0,MAX_LINKS_PER_PAGE);
      for(const h of candidates){
        if(!seen.has(h)) queue.push(h);
      }
    }catch(e){
      pages.push({requested_url:u,status:null,error:e?.name||String(e)});
    }
  }

  await Promise.allSettled(responseTasks);

  const origin=new URL(root).origin;
  const hintUrls=[...sourceHints].filter(x=>sameOrigin(x,root)).map(x=>new URL(x,root).href);
  const highHints=hintUrls.filter(likelyFeedUrl);
  const candidateUrls=[...new Set([
    ...highHints,
    ...CANDIDATE_PATHS.map(p=>origin+p)
  ])];

  if(Date.now()<deadline){
    // Explicit browser XHR sweep: up to 30 feed candidates, 6 at a time.
    const remain=deadline-Date.now();
    const subset=candidateUrls.slice(0,30);
    const xr=await xhrProbe(page,subset,deadline);
    for(const x of xr){
      if(!x.ok || x.status!==200) {
        xhrResults.push({url:x.url,ok:x.ok,error:x.error||null,status:x.status??null});
        continue;
      }
      const v=xmlValidate(x.status,x.content_type,x.body);
      xhrResults.push({
        url:x.url,ok:true,status:x.status,content_type:x.content_type,
        bytes:Buffer.byteLength(x.body||""),
        item_count_observed:v?.item_count_observed||0,
        google_merchant_valid:!!v
      });
      if(v) verified.push({site:name,discovery:"explicit-browser-XHR",url:x.url,...v,body:x.body});
    }
  }

  await ctx.close();

  const dedup=new Map();
  for(const v of verified){
    const key=v.url;
    if(!dedup.has(key) || (v.body||"").length>(dedup.get(key).body||"").length) dedup.set(key,v);
  }

  return {
    name,root,
    verified_google_xml:[...dedup.values()].map(v=>({
      discovery:v.discovery,url:v.url,status:v.status,content_type:v.content_type,
      bytes:v.bytes,item_count_observed:v.item_count_observed,
      body:v.body
    })),
    pages,
    xhr_results:xhrResults,
    source_hints:[...sourceHints].slice(0,100),
    network_requests:network.slice(0,MAX_RESPONSES),
    visited_pages:[...seen]
  };
}

async function worker(browser, queue, results){
  while(true){
    const item=queue.shift();
    if(!item) return;
    console.log("[START]",item[0]);
    const r=await probeSite(browser,item);
    console.log("[DONE]",item[0],"verified",r.verified_google_xml.length);
    results.push(r);
  }
}

async function main(){
  await fs.mkdir("out/wc-google-feed-xhr-20260927/feeds",{recursive:true});
  const browser=await chromium.launch({headless:true});
  try{
    const queue=[...TARGETS], results=[];
    await Promise.all(Array.from({length:CONCURRENCY},()=>worker(browser,queue,results)));
    for(const site of results){
      for(let i=0;i<site.verified_google_xml.length;i++){
        const v=site.verified_google_xml[i];
        const safe=site.name.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"")||"site";
        const file="out/wc-google-feed-xhr-20260927/feeds/"+safe+"-"+i+".xml";
        await fs.writeFile(file,v.body||"","utf8");
        v.artifact=file;
        delete v.body;
      }
    }
    const report={
      schema_version:"foundation-wc-google-feed-xhr-live/v1",
      generated_on:new Date().toISOString(),
      site_count:results.length,
      verified_feed_count:results.reduce((n,s)=>n+s.verified_google_xml.length,0),
      sites:results
    };
    await fs.writeFile("out/wc-google-feed-xhr-20260927/report.json",JSON.stringify(report,null,2));
    console.log(JSON.stringify({
      site_count:report.site_count,
      verified_feed_count:report.verified_feed_count,
      verified:results.flatMap(s=>s.verified_google_xml.map(v=>({site:s.name,url:v.url,discovery:v.discovery,bytes:v.bytes,item_count_observed:v.item_count_observed,artifact:v.artifact})))
    },null,2));
  }finally{
    await browser.close();
  }
}

main().catch(e=>{console.error(e);process.exit(1)});
