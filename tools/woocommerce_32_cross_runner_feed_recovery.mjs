#!/usr/bin/env node
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
const execFileAsync=promisify(execFile);

const TARGETS=[
  ["Ads Store","https://adsstore.in"],
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

const FEED_PATHS=[
 "/?woocommerce_gpf=google","/woocommerce_gpf/google",
 "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=25","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
 "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
 "/woocommerce_gpf/google?gpf_start=0&gpf_limit=25","/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
 "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250","/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
 "/google.xml","/google_feed.xml","/google-feed.xml","/google_base.xml","/googlebase.xml",
 "/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml",
 "/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml","/merchant_feed.xml",
 "/gmerchant.xml","/gpf.xml","/product-feed.xml","/products-feed.xml","/feed_products.xml","/products.xml",
 "/feed/google.xml","/feed/google-products.xml","/feeds/google.xml","/feeds/google-products.xml",
 "/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feed.xml","/rss.xml","/products.rss",
 "/feed/google","/feed/products","/products/feed","/store/feed","/?feed=google","/?feed=merchant","/?feed=products",
 "/wp-content/uploads/codesolz-feeds/google-products.xml",
 "/wp-content/uploads/woo-feed/google/xml/google.xml",
 "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
 "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
 "/wp-content/uploads/wppfm-feeds/google.xml",
 "/wp-json/feedcraft-product-feed/v1/xml"
];

function valid(body,ct){
 const x=String(body||"");
 return /base\.google\.com\/ns\/1\.0/i.test(x) &&
   /<item\b/i.test(x) &&
   /<(?:g:)?price\b/i.test(x) &&
   /<(?:g:)?(?:id|title|link)\b/i.test(x) &&
   /(xml|rss|atom)/i.test(String(ct||"")+x.slice(0,300));
}
async function fetchOne(url,ua,timeoutMs){
 const ac=new AbortController(), t=setTimeout(()=>ac.abort(),timeoutMs);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
   "User-Agent":ua,
   "Accept":"application/xml, application/rss+xml, text/xml, text/plain;q=0.9, */*;q=0.1",
   "Accept-Language":"en-IN,en;q=0.9"
  }});
  const b=Buffer.from(await r.arrayBuffer());
  return {status:r.status,url:r.url,ct:r.headers.get("content-type")||"",bytes:b.length,body:b.toString("utf8").slice(0,35000000),elapsed_ms:Date.now()- (Number(t._started)||Date.now())};
 }catch(e){return {status:0,error:e?.name||String(e),bytes:0,elapsed_ms:timeoutMs};}
 finally{clearTimeout(t);}
}
async function curlOne(url,ua,timeoutSec){
 try{
  const args=["-sS","-L","--connect-timeout","15","--max-time",String(timeoutSec),"-A",ua,
   "-H","Accept: application/xml, application/rss+xml, text/xml, text/plain;q=0.9, */*;q=0.1",
   "-H","Accept-Language: en-IN,en;q=0.9","-w","\\n__STATUS__%{http_code}\\n__URL__%{url_effective}\\n",url];
  const {stdout}=await execFileAsync("curl",args,{timeout:(timeoutSec+10)*1000,maxBuffer:40*1024*1024});
  const s=String(stdout||""), p=s.lastIndexOf("\n__STATUS__"); if(p<0)return null;
  const q=s.indexOf("\n",p+1), u=s.lastIndexOf("\n__URL__"); if(q<0||u<0)return null;
  const status=Number(s.slice(p+11,q).trim()), url2=s.slice(u+9).trim(), body=s.slice(0,p);
  return {status,url:url2,ct:"",bytes:Buffer.byteLength(body),body};
 }catch{return null;}
}
async function probe(name,base){
 const started=Date.now(), results=[];
 const roots=["/robots.txt","/sitemap.xml","/wp-sitemap.xml","/sitemap_index.xml"];
 for(const p of roots){
  const u=new URL(p,base+"/").href;
  for(const ua of [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
    "curl/8.10.1"
  ]){
   const r=await fetchOne(u,ua,30000); results.push({url:u,kind:"discovery",ua,status:r.status,ct:r.ct,bytes:r.bytes,error:r.error||null});
   if(r.status===200&&r.body){
    const found = String(r.body).split(/\s+/).map(v=>v.replace(/[),.;]+$/g,"")).filter(v=>/^https?:\/\//i.test(v)||/(google|merchant|feed|shopping|xml)/i.test(v));
    for(const v of found){
      try{
        const abs=new URL(v,base).href;
        const ah=new URL(abs).hostname.replace(/^www\\./,"");
        const bh=new URL(base).hostname.replace(/^www\\./,"");
        if(ah===bh) FEED_PATHS.push(new URL(abs).pathname+(new URL(abs).search||""));
      }catch{}
    }
   }
  }
 }
 const paths=[...new Set(FEED_PATHS)];
 const uas=[
   "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36",
   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/18.6 Safari/605.1.15",
   "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140.0 Safari/537.36"
 ];
 let verified=null;
 for(const path of paths){
  if(verified)break;
  const url=new URL(path,base+"/").href;
  for(const ua of uas){
   const r=await fetchOne(url,ua,90000);
   results.push({url,kind:"native",ua,status:r.status,ct:r.ct,bytes:r.bytes,error:r.error||null});
   if(r.status===200&&valid(r.body,r.ct)){verified={url:r.url||url,status:r.status,bytes:r.bytes,sha256:createHash("sha256").update(r.body).digest("hex")};break;}
   if(r.status===0||r.status>=400){
    const c=await curlOne(url,ua,120);
    if(c){results.push({url:c.url||url,kind:"native-curl",ua,status:c.status,ct:c.ct||"",bytes:c.bytes,error:null});
      if(c.status===200&&valid(c.body,c.ct)){verified={url:c.url||url,status:c.status,bytes:c.bytes,sha256:createHash("sha256").update(c.body).digest("hex")};break;}
    }
   }
  }
 }
 return {site:name,base,runner_os:process.env.RUNNER_OS||"unknown",verified_feed:verified,elapsed_s:Number(((Date.now()-started)/1000).toFixed(2)),
   candidate_results:results};
}
const started=Date.now(); await mkdir("out/woocommerce-32-cross-runner",{recursive:true});
const selected=process.argv.includes("--site") ? [TARGETS.find(x=>x[0].toLowerCase()===process.argv[process.argv.indexOf("--site")+1].toLowerCase())].filter(Boolean) : TARGETS;
const out=[]; for(const t of selected) out.push(await probe(...t));
await writeFile("out/woocommerce-32-cross-runner/report.json",JSON.stringify({schema_version:"woocommerce-32-cross-runner/v1",generated_on:new Date().toISOString(),results:out},null,2));
console.log(JSON.stringify({runner_os:process.env.RUNNER_OS,targets:out.length,verified:out.filter(x=>x.verified_feed).map(x=>({site:x.site,feed:x.verified_feed.url}))},null,2));
