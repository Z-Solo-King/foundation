#!/usr/bin/env node
import fs from "node:fs/promises";
import { chromium } from "playwright";

const SITE_TIMEOUT_MS = 110000;
const NAV_TIMEOUT_MS = 18000;
const SETTLE_MS = 5000;
const XHR_TIMEOUT_MS = 60000;
const MAX_PAGES = 2;
const MAX_LINKS_PER_PAGE = 12;
const CONCURRENCY = 8;

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
 "/google-products.xml",
 "/google-product-feed.xml",
 "/google.xml",
 "/google-shopping.xml",
 "/google-shopping-feed.xml",
 "/product-feed.xml",
 "/products-feed.xml",
 "/merchant-feed.xml",
 "/feed/google.xml",
 "/feeds/google.xml",
 "/feeds/google-products.xml",
 "/feeds/google-shopping.xml",
 "/wp-content/uploads/codesolz-feeds/google-products.xml",
 "/wp-content/uploads/woo-feed/google/xml/google.xml",
 "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
 "/wp-content/uploads/wppfm-feeds/google.xml"
];

function sleep(ms){ return new Promise(resolve => setTimeout(resolve, ms)); }

function isSameOrigin(url, root){
  try { return new URL(url, root).origin === new URL(root).origin; }
  catch { return false; }
}

function isGoogleLike(url){
  return /google|merchant|shopping|feed|rss|xml/i.test(url);
}

function validateMerchantXml(status, contentType, body){
  if(status !== 200 || !body) return null;
  const head = body.slice(0, 12000);
  if(!/base\.google\.com\/ns\/1\.0/i.test(head + body)) return null;
  if(!/<(?:item|entry)\b/i.test(body)) return null;
  if(!/(?:<[^>]*id\b|<[^>]*title\b|<[^>]*price\b|<[^>]*availability\b|<[^>]*condition\b)/i.test(body)) return null;
  if(!/(?:xml|rss|atom)/i.test(contentType) && !/<rss\b/i.test(head)) return null;
  const items = (body.match(/<(?:item|entry)\b/gi) || []).length;
  return {
    validation:"strict_google_merchant_xml",
    status,
    content_type:contentType,
    bytes:Buffer.byteLength(body),
    item_count_observed:items
  };
}

async function runXhrSweep(page, urls){
  return page.evaluate(async ({urls, timeout}) => {
    const one = url => new Promise(resolve => {
      const started = performance.now();
      const xhr = new XMLHttpRequest();
      let finished = false;
      const finish = value => {
        if(finished) return;
        finished = true;
        resolve(value);
      };
      const timer = setTimeout(() => finish({
        url, ok:false, error:"timeout",
        elapsed_ms:Math.round(performance.now()-started)
      }), timeout);

      try {
        xhr.open("GET", url, true);
        xhr.timeout = timeout;
        xhr.setRequestHeader("Accept","application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2");
        xhr.onload = () => {
          clearTimeout(timer);
          finish({
            url:xhr.responseURL || url,
            ok:true,
            status:xhr.status,
            content_type:xhr.getResponseHeader("content-type") || "",
            body:xhr.responseText || "",
            elapsed_ms:Math.round(performance.now()-started)
          });
        };
        xhr.onerror = () => {
          clearTimeout(timer);
          finish({url,ok:false,error:"network",elapsed_ms:Math.round(performance.now()-started)});
        };
        xhr.ontimeout = () => {
          clearTimeout(timer);
          finish({url,ok:false,error:"timeout",elapsed_ms:Math.round(performance.now()-started)});
        };
        xhr.send();
      } catch (error) {
        clearTimeout(timer);
        finish({url,ok:false,error:String(error),elapsed_ms:Math.round(performance.now()-started)});
      }
    });
    return Promise.all(urls.map(one));
  }, {urls, timeout:XHR_TIMEOUT_MS});
}

async function probeSite(browser, [name, root]){
  const started = Date.now();
  const ctx = await browser.newContext({
    userAgent:"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153 Safari/537.36",
    ignoreHTTPSErrors:true
  });
  const page = await ctx.newPage();
  const network = [];
  const networkTasks = [];
  const pages = [];
  const verified = [];
  const visited = [];
  const seen = new Set([root]);

  page.on("response", response => {
    const request = response.request();
    const type = request.resourceType();
    const url = response.url();
    const ct = response.headers()["content-type"] || "";
    network.push({url,status:response.status(),content_type:ct,resource_type:type});
    if((type === "xhr" || type === "fetch" || isGoogleLike(url)) && response.status() === 200){
      networkTasks.push((async()=>{
        try{
          const body = await response.text();
          const v = validateMerchantXml(response.status(),ct,body);
          if(v) verified.push({discovery:"page-network-xhr-fetch",url,...v,body});
        }catch{}
      })());
    }
  });

  for(let i=0;i<MAX_PAGES && Date.now()-started<SITE_TIMEOUT_MS;i++){
    const current = i === 0 ? root : [...seen][i];
    if(!current || i > 0 && !seen.has(current)) continue;
    visited.push(current);
    try{
      await page.goto(current,{waitUntil:"domcontentloaded",timeout:NAV_TIMEOUT_MS});
      await sleep(SETTLE_MS);
      const links = await page.locator("a[href]").evaluateAll(as => as.map(a => a.href).filter(Boolean));
      for(const link of links){
        if(isSameOrigin(link,root) && !seen.has(link) && /product|category|shop/i.test(link)){
          seen.add(link);
        }
      }
    }catch(error){
      pages.push({url:current,error:error?.name || String(error)});
      continue;
    }
    pages.push({url:current,final_url:page.url(),status:200});
  }

  await Promise.allSettled(networkTasks);

  const origin = new URL(root).origin;
  const candidates = CANDIDATE_PATHS.map(path => origin + path);
  const xhr = Date.now()-started < SITE_TIMEOUT_MS ? await runXhrSweep(page,candidates) : [];

  for(const result of xhr){
    const row = {
      url:result.url,
      ok:result.ok,
      status:result.status ?? null,
      content_type:result.content_type || null,
      bytes:result.ok ? Buffer.byteLength(result.body || "") : 0,
      elapsed_ms:result.elapsed_ms ?? null,
      error:result.error || null
    };
    const v = result.ok ? validateMerchantXml(result.status,result.content_type,result.body) : null;
    row.google_merchant_valid = !!v;
    row.item_count_observed = v?.item_count_observed || 0;
    if(v) verified.push({discovery:"explicit-browser-XHR",url:result.url,...v,elapsed_ms:result.elapsed_ms,body:result.body});
  }

  const dedup = new Map();
  for(const item of verified){
    const previous = dedup.get(item.url);
    if(!previous || item.bytes > previous.bytes) dedup.set(item.url,item);
  }
  await ctx.close();

  return {
    name,root,
    elapsed_ms:Date.now()-started,
    visited_pages:visited,
    pages,
    verified_google_xml:[...dedup.values()],
    xhr_results:xhr.map(r => ({
      url:r.url,ok:r.ok,status:r.status ?? null,
      content_type:r.content_type || null,
      bytes:r.ok ? Buffer.byteLength(r.body || "") : 0,
      elapsed_ms:r.elapsed_ms ?? null,
      error:r.error || null,
      google_merchant_valid:!!(r.ok && validateMerchantXml(r.status,r.content_type,r.body))
    })),
    network_requests:network
  };
}

async function worker(browser, queue, results){
  while(queue.length){
    const item=queue.shift();
    if(!item) return;
    console.log("[START]",item[0]);
    const result=await probeSite(browser,item);
    console.log("[DONE]",item[0],"verified",result.verified_google_xml.length,"elapsed_ms",result.elapsed_ms);
    results.push(result);
  }
}

async function main(){
  await fs.mkdir("out/wc-google-feed-xhr-20260927-v2/feeds",{recursive:true});
  const browser=await chromium.launch({headless:true});
  try{
    const queue=[...TARGETS], results=[];
    await Promise.all(Array.from({length:CONCURRENCY},()=>worker(browser,queue,results)));

    for(const site of results){
      for(let i=0;i<site.verified_google_xml.length;i++){
        const item=site.verified_google_xml[i];
        const safe=site.name.toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"") || "site";
        const file="out/wc-google-feed-xhr-20260927-v2/feeds/"+safe+"-"+i+".xml";
        await fs.writeFile(file,item.body || "","utf8");
        item.artifact=file;
        delete item.body;
      }
    }

    const report={
      schema_version:"foundation-wc-google-feed-xhr-live/v2",
      generated_on:new Date().toISOString(),
      site_count:results.length,
      verified_feed_count:results.reduce((n,s)=>n+s.verified_google_xml.length,0),
      sites:results
    };
    await fs.writeFile("out/wc-google-feed-xhr-20260927-v2/report.json",JSON.stringify(report,null,2));
    console.log(JSON.stringify({
      site_count:report.site_count,
      verified_feed_count:report.verified_feed_count,
      verified:results.flatMap(s=>s.verified_google_xml.map(v=>({
        site:s.name,url:v.url,discovery:v.discovery,bytes:v.bytes,item_count_observed:v.item_count_observed,elapsed_ms:v.elapsed_ms,artifact:v.artifact
      })))
    },null,2));
  }finally{
    await browser.close();
  }
}

main().catch(error=>{console.error(error);process.exit(1)});
