#!/usr/bin/env node
import fs from "node:fs/promises";

const TIMEOUT_MS = 12000;
const MAX_BODY = 1200000;
const MAX_SCRIPTS = 10;
const MAX_SITEMAPS = 12;
const CONCURRENCY = 8;

const feedPaths = [
  "/feeds/google.xml","/feed/google.xml","/google-feed.xml","/google.xml",
  "/feeds/google-shopping.xml","/feed/google-shopping.xml","/google-shopping.xml",
  "/google-shopping-feed.xml","/feeds/google-shopping-feed.xml",
  "/merchant.xml","/merchant-feed.xml","/feeds/merchant.xml","/feeds/merchant-feed.xml",
  "/product-feed.xml","/product_feed.xml","/products.xml","/feeds/products.xml",
  "/google-products.xml","/google-products-feed.xml","/datafeed/google.xml",
  "/data-feed/google.xml","/export/google.xml","/exports/google.xml",
  "/xml/google.xml","/xml/google-feed.xml","/catalog/google.xml","/catalog-feed.xml",
  "/feeds/google_merchant.xml","/feeds/google-merchant.xml","/googlemerchant.xml",
  "/google-merchant.xml","/shopping-feed.xml","/shopping_feed.xml","/feeds/shopping.xml",
  "/feed.xml","/rss.xml","/atom.xml"
];
const interesting = /(?:feed|merchant|shopping|google|productfeed|datafeed|catalogfeed|rss|atom)/i;
const googleNs = /base\.google\.com\/ns\/1\.0/i;
const itemTag = /<(?:item|entry)\b/i;
const gField = /<(?:g:|[A-Za-z_][\w.-]*:)(?:id|title|link|price|availability|condition|brand|gtin|mpn)\b/i;

function abs(s, base) {
  try { const u = new URL(s.replace(/&amp;/g, "&"), base); return /^https?:$/.test(u.protocol) ? u.href : null; }
  catch { return null; }
}
function hostEquivalent(a,b) {
  try {
    const x=new URL(a).hostname.replace(/^www\./,"");
    const y=new URL(b).hostname.replace(/^www\./,"");
    return x===y;
  } catch { return false; }
}
async function get(url, accept="*/*") {
  const c=new AbortController(), t=setTimeout(()=>c.abort(), TIMEOUT_MS);
  try {
    const r=await fetch(url,{
      redirect:"follow", signal:c.signal,
      headers:{
        "user-agent":"Mozilla/5.0 (compatible; Foundation1249FeedRecovery/1.1; +https://github.com/Z-Solo-King/foundation)",
        accept
      }
    });
    const body=await r.text();
    return {
      requested_url:url, final_url:r.url, status:r.status,
      content_type:r.headers.get("content-type")||"",
      bytes:Buffer.byteLength(body), headers:Object.fromEntries(r.headers.entries()),
      body:body.slice(0,MAX_BODY)
    };
  } catch(e) {
    return {requested_url:url,status:null,final_url:url,content_type:"",bytes:0,headers:{},body:"",error:String(e)};
  } finally { clearTimeout(t); }
}
function urlsFrom(text, base) {
  const out=new Set();
  for(const m of text.matchAll(/(?:href|src|action|content)\s*=\s*["']([^"']+)["']/gi)){ const u=abs(m[1],base); if(u) out.add(u); }
  for(const m of text.matchAll(/https?:\/\/[^\s"'<>]+/gi)){ const u=abs(m[0],base); if(u) out.add(u); }
  return [...out];
}
function sitemapUrls(text, base) {
  const out=new Set();
  for(const m of text.matchAll(/<loc>\s*([^<]+)\s*<\/loc>/gi)){ const u=abs(m[1],base); if(u) out.add(u); }
  for(const m of text.matchAll(/(?:^|\n)\s*sitemap:\s*(https?:\/\/[^\s#]+)/gi)){ const u=abs(m[1],base); if(u) out.add(u); }
  return [...out];
}
function validate(r) {
  if(r.status!==200 || !r.body) return null;
  if(!googleNs.test(r.body) || !itemTag.test(r.body) || !gField.test(r.body)) return null;
  const count=(r.body.match(/<(?:item|entry)\b/g)||[]).length;
  return count ? {
    url:r.final_url||r.requested_url,status:r.status,content_type:r.content_type,
    bytes:r.bytes,item_count_observed:count,
    google_namespace:"http://base.google.com/ns/1.0",
    validation:"strict_google_merchant_xml"
  } : null;
}
async function mapLimit(items,fn,limit=CONCURRENCY){
  const out=new Array(items.length); let cursor=0;
  async function worker(){ while(true){ const i=cursor++; if(i>=items.length) return; out[i]=await fn(items[i],i); } }
  await Promise.all(Array.from({length:Math.min(limit,items.length)},worker)); return out;
}
async function probeRoot(root){
  const result={root,verified_google_xml:[],public_json_surfaces:[],candidate_count:0,transport:{}};
  const home=await get(root,"text/html,application/xml;q=0.9,*/*;q=0.3");
  result.transport.homepage={status:home.status,content_type:home.content_type,bytes:home.bytes,final_url:home.final_url,error:home.error||null};
  if(home.status!==200) return result;

  const linked=urlsFrom(home.body,root).filter(u=>hostEquivalent(u,root));
  const scripts=[...new Set(linked.filter(u=>/\.m?js(?:[?#]|$)/i.test(u)))].slice(0,MAX_SCRIPTS);
  const scriptResponses=await mapLimit(scripts,u=>get(u,"text/javascript,*/*;q=0.2"),4);

  const robots=await get(new URL("/robots.txt",root).href,"text/plain,*/*;q=0.2");
  result.transport.robots={status:robots.status,content_type:robots.content_type,bytes:robots.bytes,final_url:robots.final_url,error:robots.error||null};

  const sitemapSeeds=[...new Set([
    ...sitemapUrls(robots.body||"",root),
    ...sitemapUrls(home.body||"",root),
    "/sitemap.xml","/sitemap_index.xml","/sitemap-index.xml","/sitemap/sitemap.xml",
    "/sitemap_products.xml","/sitemap-pages.xml","/sitemap_categories.xml","/sitemap_collections.xml"
  ].map(x=>abs(x,root)).filter(Boolean))];

  const sourceHits=[];
  for(const [kind,text] of [["homepage",home.body||""],["robots",robots.body||""],...scriptResponses.map((x,i)=>["script_"+i,x.body||""])]){
    for(const m of text.matchAll(/.{0,120}(?:google|merchant|shopping|feed|rss|atom|xml).{0,180}/ig)){
      sourceHits.push({kind,snippet:m[0].replace(/\\s+/g," ").slice(0,350)});
      if(sourceHits.length>=80) break;
    }
    if(sourceHits.length>=80) break;
  }
  result.source_hits=sourceHits;

  const discoveredFeedUrls=new Set();
  for(const source of [home.body||"",robots.body||"",...scriptResponses.filter(x=>x.status===200).map(x=>x.body||"")]){
    for(const u of urlsFrom(source,root)){
      if(interesting.test(u)) discoveredFeedUrls.add(u);
    }
  }

  const sitemapBodies=[];
  for(const seed of sitemapSeeds.slice(0,MAX_SITEMAPS)){
    const sr=await get(seed,"application/xml,text/xml,*/*;q=0.2");
    if(sr.status===200 && /xml/i.test(sr.content_type+seed)){
      sitemapBodies.push(sr.body||"");
      for(const u of sitemapUrls(sr.body||"",seed)) if(interesting.test(u)) discoveredFeedUrls.add(u);
    }
  }

  const candidates=new Set(feedPaths.map(p=>abs(p,root)).filter(Boolean));
  for(const u of discoveredFeedUrls){
    if(hostEquivalent(u,root) || /(?:hyperinvento|feed|shopping|merchant|google)/i.test(new URL(u).hostname)) candidates.add(u);
  }

  const responses=await mapLimit([...candidates], async u=>{
    const r=await get(u,"application/xml,text/xml,application/rss+xml,application/atom+xml,*/*;q=0.1");
    const v=validate(r); if(v) result.verified_google_xml.push(v);
    if(r.status===200 && /json/i.test(r.content_type)) result.public_json_surfaces.push({url:r.final_url||u,status:r.status,content_type:r.content_type,bytes:r.bytes});
    const bodySnippet = (r.status===200 && (/xml/i.test(r.content_type) || /^\\s*<\\?xml/i.test(r.body||"") || /^\\s*<(?:rss|feed|sitemap)/i.test(r.body||"")))
      ? (r.body||"").slice(0,2500)
      : null;
    return {url:r.final_url||u,status:r.status,content_type:r.content_type,bytes:r.bytes,verified:!!v,error:r.error||null,body_snippet:bodySnippet};
  });
  result.candidate_count=responses.length;
  result.responses=responses;
  return result;
}

async function main(){
  const input=JSON.parse(await fs.readFile(process.argv[2],"utf8"));
  const sites=await mapLimit(input.sites, async site=>{
    const roots=await mapLimit(site.roots,probeRoot,3);
    return {
      name:site.name,roots:site.roots,
      verified_google_xml:roots.flatMap(x=>x.verified_google_xml),
      public_json_surfaces:roots.flatMap(x=>x.public_json_surfaces),
      root_results:roots
    };
  },5);
  const verified=sites.flatMap(s=>s.verified_google_xml.map(v=>({...v,site:s.name})));
  const report={
    schema_version:"foundation-custom-api-google-feed-live/v2",
    generated_on:new Date().toISOString(),issue:1249,sites:sites.length,
    verified_google_xml:verified,results:sites
  };
  await fs.writeFile(process.argv[3],JSON.stringify(report,null,2));
  console.log(JSON.stringify({
    issue:1249,sites:sites.length,verified_feed_count:verified.length,
    verified_feeds:verified
  },null,2));
}
main().catch(e=>{console.error(e);process.exit(1)});
