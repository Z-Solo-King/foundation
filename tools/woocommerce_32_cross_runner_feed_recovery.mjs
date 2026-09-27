#!/usr/bin/env node
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
const execFileAsync=promisify(execFile);
const UA = "Mozilla/5.0 (compatible; WooCommerceV175Recovery/2026.09)";

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

async function storeApiProbe(base){
  const endpoints=[
    `${base}/wp-json/wc/store/v1/products`,
    `${base}/wp-json/wc/store/v1/products/`,
    `${base}/?rest_route=/wc/store/v1/products`,
    `${base}/wp-json/wp/v2/product`,
    `${base}/wp-json/wp/v2/products`
  ];
  function rows(data){
    const a=Array.isArray(data)?data:(data?.products||data?.items||data?.results||data?.data||[]);
    if(!Array.isArray(a)) return [];
    return a.map(p=>{
      const prices=p?.prices||{};
      const minor=Number(prices.currency_minor_unit ?? 2);
      const raw=prices.price ?? p.price ?? p.sale_price ?? p.regular_price ?? "";
      let n=Number(String(raw).replace(/,/g,""));
      if(Number.isFinite(n) && prices.price!==undefined) n/=Math.pow(10,minor);
      const link=p.permalink||p.url||p.link||"";
      const title=p.name||p.title||"";
      return {
        id:String(p.id??p.sku??p.slug??""),
        title:String(title),
        link:String(link),
        price:Number.isFinite(n)?n:"",
        currency:String(prices.currency_code||p.currency||"INR"),
        availability:(p.is_in_stock===false||p.stock_status==="outofstock")?"out of stock":"in stock",
        image:String(p?.images?.[0]?.src||p?.images?.[0]?.url||p.image||p.image_url||""),
        description:String(p.short_description||p.description||""),
        brand:String(p?.brand?.name||p?.brands?.[0]?.name||p.brand||""),
        sku:String(p.sku||"")
      };
    }).filter(x=>x.title&&x.link);
  }
  for(const ep of endpoints){
    let first=null;
    for(const q of ["?per_page=100&page=1","?page=1&per_page=100",""]){
      const r=await fetchOne(ep+q,UA,90000);
      if(r.status!==200||!r.body) continue;
      try{
        const rs=rows(JSON.parse(r.body));
        if(!rs.length) continue;
        const all=[...rs];
        for(let page=2;page<=100;page++){
          const rr=await fetchOne(ep+"?per_page=100&page="+page,UA,90000);
          if(rr.status!==200||!rr.body) break;
          let more=[]; try{more=rows(JSON.parse(rr.body))}catch{break;}
          if(!more.length) break;
          all.push(...more);
          if(more.length<100) break;
        }
        const seen=new Set(), uniqRows=all.filter(x=>{const k=x.id||x.link||x.title;if(seen.has(k))return false;seen.add(k);return true;});
        if(uniqRows.length) return {endpoint:ep,count:uniqRows.length,rows:uniqRows};
      }catch{}
    }
  }
  return null;
}


async function listingPdpProbe(base){
  const listingPaths=["/","/shop/","/products/","/store/","/?post_type=product","/product-category/"];
  const seen=new Set(), productUrls=[];
  const addLinks=(html)=>{
    for(const m of String(html||"").matchAll(/(?:href|data-href)=["']([^"']+)["']/gi)){
      try{
        const u=new URL(m[1],base).href;
        const h=new URL(u).hostname.replace(/^www\./,"");
        const bh=new URL(base).hostname.replace(/^www\./,"");
        if(h===bh && /\/product\//i.test(new URL(u).pathname) && !seen.has(u)){
          seen.add(u); productUrls.push(u);
        }
      }catch{}
    }
  };
  for(const p of listingPaths){
    const r=await fetchOne(new URL(p,base+"/").href,UA,45000);
    if(r.status!==200||!r.body) continue;
    addLinks(r.body);
    if(productUrls.length>=120) break;
  }
  if(!productUrls.length) return null;
  function cleanText(s){return String(s||"").replace(/<script[\s\S]*?<\/script>/gi," ").replace(/<style[\s\S]*?<\/style>/gi," ").replace(/<[^>]+>/g," ").replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&").replace(/\s+/g," ").trim();}
  function getAttr(h,p){const m=h.match(p);return m?m[1]:"";}
  const rows=[];
  for(const u of productUrls.slice(0,100)){
    const r=await fetchOne(u,UA,45000); if(r.status!==200||!r.body) continue;
    const h=r.body;
    const title=getAttr(h,/<h1[^>]*class=["'][^"']*(?:product_title|product-title|entry-title)[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i) || getAttr(h,/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)/i) || (h.match(/<title[^>]*>([\s\S]*?)<\/title>/i)||[])[1]||"";
    const image=getAttr(h,/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)/i) || getAttr(h,/<img[^>]+(?:data-large_image|data-src|src)=["']([^"']+)["']/i);
    const desc=getAttr(h,/<meta[^>]+property=["']og:description["'][^>]+content=["']([^"']+)/i);
    const pc=[
      getAttr(h,/<meta[^>]+(?:property|name)=["']product:price:amount["'][^>]+content=["']([^"']+)/i),
      getAttr(h,/<meta[^>]+itemprop=["']price["'][^>]+content=["']([^"']+)/i),
      getAttr(h,/<span[^>]+class=["'][^"']*woocommerce-Price-amount[^"']*["'][^>]*>[\s\S]*?<bdi>[\s\S]*?([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i),
      getAttr(h,/<(?:div|span|p)[^>]+class=["'][^"']*(?:price|amount)[^"']*["'][^>]*>[\s\S]*?([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i)
    ].filter(Boolean);
    const price=pc.length?Number(pc[0].replace(/,/g,"")):NaN;
    if(!title||!image||!Number.isFinite(price)) continue;
    const sku=getAttr(h,/data-product_sku=["']([^"']*)["']/i)||getAttr(h,/<meta[^>]+itemprop=["']sku["'][^>]+content=["']([^"']+)/i);
    rows.push({id:String(sku||u),title:cleanText(title),description:cleanText(desc||title).slice(0,5000),link:u,image,price,currency:"INR",availability:/out[- ]of[- ]stock|outofstock/i.test(h)?"out of stock":"in stock",brand:"",sku});
    if(rows.length>=100) break;
  }
  return rows.length?{count:rows.length,rows}:null;
}

async function sitemapPdpProbe(base){
  const sitemapUrls=[
    `${base}/wp-sitemap-posts-product-1.xml`,
    `${base}/product-sitemap.xml`,
    `${base}/product-sitemap1.xml`,
    `${base}/sitemap-products.xml`,
    `${base}/sitemap.xml`,
    `${base}/sitemap_index.xml`,
    `${base}/wp-sitemap.xml`
  ];
  const seenUrls=new Set(), productUrls=[];
  for(const sm of [...new Set(sitemapUrls)]){
    const r=await fetchOne(sm,UA,45000);
    if(r.status!==200||!r.body) continue;
    for(const m of r.body.matchAll(/<loc>\s*(https?:\/\/[^<]+)\s*<\/loc>/gi)){
      const u=m[1].trim();
      if(/\/product\/|product-|\/p\//i.test(u) && !seenUrls.has(u)){
        seenUrls.add(u); productUrls.push(u);
      }
    }
    if(productUrls.length>=200) break;
  }
  if(!productUrls.length) return null;
  function cleanText(s){
    return String(s||"").replace(/<script[\s\S]*?<\/script>/gi," ")
      .replace(/<style[\s\S]*?<\/style>/gi," ")
      .replace(/<[^>]+>/g," ")
      .replace(/&nbsp;/gi," ").replace(/&amp;/gi,"&")
      .replace(/\s+/g," ").trim();
  }
  function getAttr(h,pattern){const m=h.match(pattern);return m?m[1]:"";}
  const rows=[];
  for(const u of productUrls.slice(0,120)){
    const r=await fetchOne(u,UA,45000);
    if(r.status!==200||!r.body) continue;
    const h=r.body;
    const title=getAttr(h,/<h1[^>]*class=["'][^"']*(?:product_title|product-title|entry-title)[^"']*["'][^>]*>([\s\S]*?)<\/h1>/i)
      || getAttr(h,/<meta[^>]+property=["']og:title["'][^>]+content=["']([^"']+)/i)
      || (h.match(/<title[^>]*>([\s\S]*?)<\/title>/i)||[])[1] || "";
    const image=getAttr(h,/<meta[^>]+property=["']og:image["'][^>]+content=["']([^"']+)/i)
      || getAttr(h,/<img[^>]+(?:data-large_image|data-src|src)=["']([^"']+)["']/i);
    const desc=getAttr(h,/<meta[^>]+property=["']og:description["'][^>]+content=["']([^"']+)/i);
    const priceCandidates=[
      getAttr(h,/<meta[^>]+(?:property|name)=["']product:price:amount["'][^>]+content=["']([^"']+)/i),
      getAttr(h,/<meta[^>]+itemprop=["']price["'][^>]+content=["']([^"']+)/i),
      getAttr(h,/<span[^>]+class=["'][^"']*woocommerce-Price-amount[^"']*["'][^>]*>[\s\S]*?<bdi>[\s\S]*?([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i),
      getAttr(h,/<(?:div|span|p)[^>]+class=["'][^"']*(?:price|amount)[^"']*["'][^>]*>[\s\S]*?([0-9][0-9,]*(?:\.[0-9]{1,2})?)/i)
    ].filter(Boolean);
    const price=priceCandidates.length ? Number(priceCandidates[0].replace(/,/g,"")) : NaN;
    if(!title||!image||!Number.isFinite(price)) continue;
    const sku=getAttr(h,/data-product_sku=["']([^"']*)["']/i) || getAttr(h,/<meta[^>]+itemprop=["']sku["'][^>]+content=["']([^"']+)/i);
    rows.push({
      id:String(sku||u),
      title:cleanText(title),
      description:cleanText(desc||title).slice(0,5000),
      link:u,
      image,
      price,
      currency:"INR",
      availability:/out[- ]of[- ]stock|outofstock/i.test(h) ? "out of stock" : "in stock",
      brand:"",
      sku
    });
    if(rows.length>=100) break;
  }
  return rows.length ? {count:rows.length,rows} : null;
}

function xmlEscape(v){return String(v??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&apos;");}
function rowsToGoogleBackup(rows){
  return `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:g="http://base.google.com/ns/1.0"><channel>
<title>WooCommerce public Store API recovery snapshot</title>
<link></link><description>Reconstructed public snapshot; not retailer-native.</description>
${rows.map(r=>`<item><g:id>${xmlEscape(r.id)}</g:id><g:title>${xmlEscape(r.title)}</g:title><g:link>${xmlEscape(r.link)}</g:link><g:price>${xmlEscape(Number(r.price||0).toFixed(2))} ${xmlEscape(r.currency||"INR")}</g:price><g:availability>${xmlEscape(r.availability)}</g:availability>${r.image?`<g:image_link>${xmlEscape(r.image)}</g:image_link>`:""}${r.brand?`<g:brand>${xmlEscape(r.brand)}</g:brand>`:""}${r.sku?`<g:mpn>${xmlEscape(r.sku)}</g:mpn>`:""}${r.description?`<description>${xmlEscape(r.description.replace(/<[^>]+>/g," ").slice(0,5000))}</description>`:""}</item>`).join("\\n")}
</channel></rss>\\n`;
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
   if(r.status===200&&valid(r.body,r.ct)){verified={url:r.url||url,status:r.status,bytes:r.bytes,item_count:(r.body.match(/<item\\b/gi)||[]).length,sha256:createHash("sha256").update(r.body).digest("hex")};break;}
   if(r.status===0||r.status>=400){
    const c=await curlOne(url,ua,120);
    if(c){results.push({url:c.url||url,kind:"native-curl",ua,status:c.status,ct:c.ct||"",bytes:c.bytes,error:null});
      if(c.status===200&&valid(c.body,c.ct)){verified={url:c.url||url,status:c.status,bytes:c.bytes,item_count:(c.body.match(/<item\\b/gi)||[]).length,sha256:createHash("sha256").update(c.body).digest("hex")};break;}
    }
   }
  }
 }
 const api=await storeApiProbe(base);
 const pdp=!api?await sitemapPdpProbe(base):null;
 const listing=!api&&!pdp?await listingPdpProbe(base):null;
 return {site:name,base,runner_os:process.env.RUNNER_OS||"unknown",verified_feed:verified,public_store_api:api?{endpoint:api.endpoint,count:api.count}:null,pdp_recovery:pdp?{count:pdp.count}:null,listing_recovery:listing?{count:listing.count}:null,recovery_method:api?'store_api':pdp?'sitemap_pdp':listing?'listing_pdp':null,backup_google_xml:api?rowsToGoogleBackup(api.rows):(pdp?rowsToGoogleBackup(pdp.rows):(listing?rowsToGoogleBackup(listing.rows):null)),elapsed_s:Number(((Date.now()-started)/1000).toFixed(2)),
   candidate_results:results};
}
const started=Date.now(); await mkdir("out/woocommerce-32-cross-runner",{recursive:true});
const selected=process.argv.includes("--site") ? [TARGETS.find(x=>x[0].toLowerCase()===process.argv[process.argv.indexOf("--site")+1].toLowerCase())].filter(Boolean) : TARGETS;
const out=[]; for(const t of selected){
  const r=await probe(...t); out.push(r);
  if(r.backup_google_xml){ const slug=r.site.toLowerCase().replace(/[^a-z0-9]+/g,"-"); await writeFile("out/woocommerce-32-cross-runner/"+slug+"-store-api-backup.xml",r.backup_google_xml); }
}
await writeFile("out/woocommerce-32-cross-runner/report.json",JSON.stringify({schema_version:"woocommerce-32-cross-runner/v2",generated_on:new Date().toISOString(),results:out.map(({backup_google_xml,...rest})=>({...rest,backup_google_xml_file:backup_google_xml?rest.site.toLowerCase().replace(/[^a-z0-9]+/g,"-")+"-store-api-backup.xml":null}))},null,2));
console.log(JSON.stringify({runner_os:process.env.RUNNER_OS,targets:out.length,native_verified:out.filter(x=>x.verified_feed).map(x=>({site:x.site,feed:x.verified_feed.url,items:x.verified_feed.item_count})),store_api_backups:out.filter(x=>x.public_store_api).map(x=>({site:x.site,endpoint:x.public_store_api.endpoint,count:x.public_store_api.count})),unresolved:out.filter(x=>!x.verified_feed&&!x.public_store_api).map(x=>x.site)},null,2));
