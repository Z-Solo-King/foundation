#!/usr/bin/env node
import fs from "node:fs/promises";
import { chromium } from "playwright";
import { mapBounded } from "./bounded_parallel.mjs";

const NAV_TIMEOUT = 20000, SETTLE_MS = 5000, MAX_PAGES = 5, MAX_LINKS = 25, MAX_RESPONSES = 450;
const SITE_CONCURRENCY = Math.max(1, Number(process.env.SITE_CONCURRENCY || 4));
const REGISTRY = "data/feed_lab/commerce_feed_targets.json";

function sleep(ms){return new Promise(r=>setTimeout(r,ms));}
function publicLink(h,root){
  try{
    const u=new URL(h,root), r=new URL(root);
    return /^https?:$/.test(u.protocol) &&
      u.hostname.replace(/^www\./,"")===r.hostname.replace(/^www\./,"") &&
      !/\/wp-(?:admin|login)|\/cart(?:\/|$)|\/checkout(?:\/|$)|\/my-account(?:\/|$)/i.test(u.pathname);
  }catch{return false}
}
function score(h){
  const p=new URL(h).pathname.toLowerCase(); let s=0;
  if(/\/product\//.test(p)||/\/products?\//.test(p))s+=10;
  if(/\/product-category\//.test(p)||/\/category\//.test(p))s+=8;
  if(/\/shop\/?$/.test(p))s+=6;
  return s;
}
function valid(status,ct,body){
  if(status!==200||!body)return null;
  if(!/base\.google\.com\/ns\/1\.0/i.test(body)||!/<(?:item|entry)\b/i.test(body))return null;
  if(!/(?:<g:)?(?:id|title|price|availability|condition)\b/i.test(body))return null;
  const count=(body.match(/<(?:item|entry)\b/g)||[]).length;
  return count?{status,content_type:ct,bytes:Buffer.byteLength(body),item_count_observed:count,validation:"strict_google_merchant_xml"}:null;
}
function publicPlatform(body,urls){
  const x=String(body||"")+"\n"+urls.join("\n");
  if(/woocommerce|wc-ajax|wp-json\/wc/i.test(x))return"woocommerce";
  if(/_next\/|__NEXT_DATA__/i.test(x))return"nextjs";
  if(/graphql|magento/i.test(x))return"magento";
  if(/dotshowroom|dotpe/i.test(x))return"dotshowroom";
  if(/hyperinvento/i.test(x))return"hyperinvento";
  return null;
}
async function siteProbe(browser,site){
  const roots=[];
  for(const root of site.roots){
    const context=await browser.newContext({userAgent:"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"});
    const page=await context.newPage(), queue=[root], seen=new Set(), visited=[], net=[], verified=[], json=[], interesting=[];
    const onResponse=async response=>{
      if(net.length>=MAX_RESPONSES)return;
      const u=response.url(), status=response.status(), ct=response.headers()["content-type"]||"", type=response.request().resourceType();
      net.push({url:u,status,content_type:ct,resource_type:type});
      try{
        if(status===200 && (/xml|rss|atom/i.test(ct)||/feed|merchant|google|shopping/i.test(u))){
          const body=await response.text(), v=valid(status,ct,body); if(v)verified.push({url:u,...v});
        }
      }catch{}
      if(status===200&&/json/i.test(ct))json.push({url:u,status,content_type:ct,resource_type:type});
      if(/(?:feed|merchant|shopping|google|xml|rss|atom)/i.test(u+ct)){
        interesting.push({url:u,status,content_type:ct,resource_type:type});
      }
    };
    page.on("response",onResponse);
    for(let i=0;i<MAX_PAGES&&queue.length;i++){
      const u=queue.shift(); if(seen.has(u))continue; seen.add(u);
      try{
        const response=await page.goto(u,{waitUntil:"domcontentloaded",timeout:NAV_TIMEOUT}); await sleep(SETTLE_MS);
        const html=await page.content();
        const links=await page.locator("a[href]").evaluateAll(as=>as.map(a=>a.href).filter(Boolean));
        visited.push({requested_url:u,final_url:page.url(),status:response?.status()??null,platform:publicPlatform(html,links)});
        for(const h of links.filter(h=>publicLink(h,root)).sort((a,b)=>score(b)-score(a)).slice(0,MAX_LINKS)){
          if(score(h)>0&&!seen.has(h))queue.push(h);
        }
      }catch(e){visited.push({requested_url:u,status:null,error:e?.name||String(e)});}
    }
    await context.close();
    roots.push({root,visited,network_requests:net,interesting_responses:[...new Map(interesting.map(x=>[x.url,x])).values()].slice(0,200),verified_google_xml:[...new Map(verified.map(x=>[x.url,x])).values()],public_json_requests:[...new Map(json.map(x=>[x.url,x])).values()],visited_pages:[...seen]});
  }
  return {name:site.name,roots:roots,verified_google_xml:roots.flatMap(x=>x.verified_google_xml),visited_pages:roots.flatMap(x=>x.visited_pages)};
}
async function main(){
  const input=JSON.parse(await fs.readFile(REGISTRY,"utf8"));
  const sites=Array.isArray(input.targets) ? input.targets.map(([name,root])=>({name,roots:[root]})) : [];
  if(!sites.length) throw new Error("private feed target registry is empty");
  await fs.mkdir("out/custom-feed-crawl",{recursive:true});
  const browser=await chromium.launch({headless:true});
  try{
    const results=await mapBounded(sites,SITE_CONCURRENCY,s=>siteProbe(browser,s));
    const verified=results.flatMap(x=>x.verified_google_xml);
    const report={
      schema_version:"foundation-custom-feed-product-crawl/v1",
      generated_on:new Date().toISOString(),
      target_count:results.length,
      site_concurrency:SITE_CONCURRENCY,
      verified_feed_count:verified.length,
      visited_page_count:results.reduce((n,x)=>n+x.visited_pages.length,0),
      successful_target_count:results.filter(x=>x.visited_pages.some(v=>v.status===200)).length
    };
    await fs.writeFile("out/custom-feed-crawl/report.json",JSON.stringify(report,null,2)+"\n");
    console.log(JSON.stringify(report,null,2));
  }finally{await browser.close();}
}
main().catch(e=>{console.error(e);process.exit(1)});