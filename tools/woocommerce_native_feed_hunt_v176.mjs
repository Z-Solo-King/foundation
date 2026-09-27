#!/usr/bin/env node
const sites = JSON.parse(process.env.SITES_JSON || "[]");
const browserWorker = process.env.BROWSER_WORKER_URL || "";
const groqKey = process.env.GROQ_API_KEY || "";

const hints = [
  "/?woocommerce_gpf=google","/woocommerce_gpf/google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=25","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
  "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250","/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
  "/google.xml","/google_feed.xml","/google-feed.xml","/google_base.xml","/googlebase.xml",
  "/google-products.xml","/google-product-feed.xml","/google_product_feed.xml",
  "/google-shopping.xml","/google-shopping-feed.xml","/google-shopping-products.xml",
  "/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml","/merchant_feed.xml",
  "/gmerchant.xml","/gpf.xml","/product-feed.xml","/products-feed.xml","/feed_products.xml",
  "/feeds/google.xml","/feeds/google_feed.xml","/feeds/google_base.xml","/feeds/google-products.xml",
  "/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml",
  "/feeds/google-merchant.xml","/feeds/google-merchant-feed.xml","/feeds/merchant.xml","/feeds/merchant-feed.xml",
  "/feed/google.xml","/feed/google-feed.xml","/feed/google-products.xml","/feed/google-product-feed.xml",
  "/feed/google-shopping.xml","/feed/google-shopping-feed.xml","/feed/merchant.xml","/feed/merchant-feed.xml",
  "/product-feed/google.xml","/product-feed/google-shopping.xml","/catalog/feed","/catalog/feed.xml",
  "/catalog/google.xml","/media/feed/google.xml",
  "/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml","/wp-content/uploads/google_product_feed.xml",
  "/wp-content/uploads/google-shopping.xml","/wp-content/uploads/codesolz-feeds/google.xml",
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/woo-feed/google/xml/google.xml",
  "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml","/wp-content/uploads/wppfm-feeds/google.xml",
  "/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/google.xml",
  "/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml","/wp-json/woo-feed/v1/google.xml"
];

const sleep = ms => new Promise(r => setTimeout(r, ms));
function sameHost(a,b){try{return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}catch{return false}}
function candidateUrl(root,p){try{return new URL(p,root.endsWith("/")?root:root+"/").href}catch{return null}}
function nativeValid(body, ct=""){
  const s=String(body||"");
  if(!/^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(s)) return false;
  if(!/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(s)) return false;
  if(!/<item\b/i.test(s)) return false;
  if(!/<g:id\b/i.test(s)||!/<g:title\b/i.test(s)||!/<g:link\b/i.test(s)) return false;
  if(!/<g:price\b/i.test(s)||!/<g:availability\b/i.test(s)) return false;
  if(/just a moment|cf-chl-|turnstile|captcha|access denied|attention required/i.test(s)) return false;
  return true;
}
async function direct(url,timeout=120000){
  const ac=new AbortController(), timer=setTimeout(()=>ac.abort(),timeout);
  try{
    const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
      "User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedHunt/2026.09)",
      "Accept":"application/xml,application/rss+xml,text/xml,text/html;q=.8,*/*;q=.2",
      "Accept-Language":"en-IN,en;q=.9"
    }});
    const body=await r.text();
    return {status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body};
  }catch(e){return {status:0,error:String(e?.name||e)}}
  finally{clearTimeout(timer)}
}
async function browser(url){
  if(!browserWorker) return null;
  const endpoint=browserWorker.replace(/\/$/,"")+"?u="+encodeURIComponent(url);
  const r=await direct(endpoint,90000);
  if(r.status!==200) return null;
  try{const d=JSON.parse(r.body); return d?.success ? String(d.result||"") : null}catch{return null}
}
function xmlUrls(text,root){
  const out=[];
  for(const m of String(text||"").matchAll(/https?:\/\/[^\s"'<>]+/gi)){
    const u=m[0].replace(/[),.;]+$/,"");
    if(sameHost(u,root)&&/\.xml(?:\.gz)?(?:$|[?#])/i.test(u)) out.push(u);
  }
  for(const m of String(text||"").matchAll(/(?:href|loc)=["']([^"']+)["']/gi)){
    const u=candidateUrl(root,m[1]);
    if(u&&sameHost(u,root)&&/\.xml(?:\.gz)?(?:$|[?#])/i.test(u)) out.push(u);
  }
  return out;
}
async function groqCandidates(root, text){
  if(!groqKey||!text) return [];
  const prompt = `We are searching one retailer for its EXISTING native Google Merchant product XML feed URL. Domain: ${root}
Below is public page text/markup. Identify ONLY feed URLs explicitly present or strongly referenced by this content. Do not invent URLs. Return JSON array of URL strings. Exclude sitemaps, RSS, Atom, Store API, JSON APIs, reconstructed feeds, and product pages.
CONTENT:
${String(text).slice(0,24000)}`;
  try{
    const r=await fetch("https://api.groq.com/openai/v1/chat/completions",{
      method:"POST",headers:{"Authorization":"Bearer "+groqKey,"Content-Type":"application/json"},
      body:JSON.stringify({model:"llama-3.3-70b-versatile",temperature:0,response_format:{type:"json_object"},
        messages:[{role:"system",content:"Return only JSON object {urls:[string,...]}."},{role:"user",content:prompt}]})
    });
    if(!r.ok)return [];
    const d=await r.json(), c=d?.choices?.[0]?.message?.content||"{}";
    const j=JSON.parse(c); return Array.isArray(j.urls)?j.urls:[];
  }catch{return []}
}
async function probe(site){
  const root=site.url.replace(/\/$/,"");
  const candidates=[...hints.map(p=>candidateUrl(root,p)).filter(Boolean)];
  const discoveryPages=["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml"];
  const discovery=[];
  for(const p of discoveryPages){
    const u=root+p;
    const [d,b]=await Promise.all([direct(u,30000),browser(u)]);
    const texts=[d.status===200?d.body:"",b||""].filter(Boolean);
    for(const t of texts)candidates.push(...xmlUrls(t,root));
    const ai=await groqCandidates(root,texts.join("\n").slice(0,24000));
    for(const u2 of ai){try{const abs=new URL(u2,root).href;if(sameHost(abs,root))candidates.push(abs)}catch{}}
    discovery.push({url:u,direct_status:d.status,browser_seen:Boolean(b)});
  }
  const uniq=[...new Set(candidates)].filter(u=>sameHost(u,root));
  for(const u of uniq){
    let r=await direct(u,120000);
    if(r.status===200&&sameHost(r.url,u)&&nativeValid(r.body,r.ct))
      return {site:site.name,url:r.url,method:"direct",tested:uniq.length,discovery};
    if(browserWorker && /\.xml(?:\.gz)?(?:$|[?#])/i.test(u)){
      const x=await browser(u);
      if(x&&nativeValid(x,"application/xml"))
        return {site:site.name,url:u,method:"cloudflare_browser",tested:uniq.length,discovery};
    }
    await sleep(75);
  }
  return {site:site.name,url:null,method:null,tested:uniq.length,discovery};
}
const results=[];
for(const site of sites){ results.push(await probe(site)); }
console.log(JSON.stringify({native_google_xml_only:true,results},null,2));
