#!/usr/bin/env node
const sites=JSON.parse(process.env.SITES_JSON||"[]"), BW=(process.env.BROWSER_WORKER_URL||"").replace(/\/$/,""), GROQ=process.env.GROQ_API_KEY||"";
const H=[
"/?woocommerce_gpf=google","/woocommerce_gpf/google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
"/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000","/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
"/google.xml","/google_feed.xml","/google-feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml",
"/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml",
"/merchant-feed.xml","/gpf.xml","/product-feed.xml","/products-feed.xml","/feeds/google.xml","/feeds/google-products.xml",
"/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml","/feed/google.xml",
"/feed/google-products.xml","/feed/google-product-feed.xml","/feed/google-shopping.xml","/feed/google-shopping-feed.xml",
"/feed/merchant.xml","/feed/merchant-feed.xml","/catalog/feed.xml","/catalog/google.xml","/media/feed/google.xml",
"/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml","/wp-content/uploads/google_product_feed.xml",
"/wp-content/uploads/codesolz-feeds/google.xml","/wp-content/uploads/codesolz-feeds/google-products.xml",
"/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/woo-feed/google/xml/google.xml",
"/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
"/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
"/wp-content/uploads/wppfm-feeds/google.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/google.xml",
"/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml","/wp-json/woo-feed/v1/google.xml"];
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,"")==new URL(b).hostname.replace(/^www\./,"")}catch{return false}};
const abs=(r,p)=>{try{return new URL(p,r).href}catch{return null}};
const valid=s=>/^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(s)&&/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(s)&&/<item\b/i.test(s)&&/<g:id\b/i.test(s)&&/<g:title\b/i.test(s)&&/<g:link\b/i.test(s)&&/<g:price\b/i.test(s)&&/<g:availability\b/i.test(s)&&!/just a moment|cf-chl-|turnstile|captcha|access denied|attention required/i.test(s);
async function get(u,ms=30000){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(u,{redirect:"follow",signal:c.signal,headers:{"User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedHunt/2026.09)","Accept":"application/xml,application/rss+xml,text/xml,text/html;q=.7,*/*;q=.2","Accept-Language":"en-IN,en;q=.9"}});return{status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body:await r.text()}}catch(e){return{status:0,error:String(e?.name||e)}}finally{clearTimeout(t)}}
async function browser(u){if(!BW)return null;const r=await get(BW+"?u="+encodeURIComponent(u),50000);if(r.status!==200)return null;try{const d=JSON.parse(r.body);return d?.success?String(d.result||""):null}catch{return null}}
function xmls(s,r){const o=[];for(const m of String(s||"").matchAll(/https?:\/\/[^\s"'<>]+/gi)){const u=m[0].replace(/[),.;]+$/,"");if(same(u,r)&&/\.xml(?:\.gz)?(?:$|[?#])/i.test(u))o.push(u)}for(const m of String(s||"").matchAll(/(?:href|loc)=["']([^"']+)["']/gi)){const u=abs(r,m[1]);if(u&&same(u,r)&&/\.xml(?:\.gz)?(?:$|[?#])/i.test(u))o.push(u)}return o}
async function ai(r,s){if(!GROQ||!s)return[];try{const q=`Domain ${r}. From this public content, return only explicitly present URLs for a native Google Merchant product XML feed on this same host. Never invent. Exclude sitemaps, RSS, Atom, JSON APIs, Store API and product pages. JSON: {"urls":["..."]}. CONTENT:\n${String(s).slice(0,16000)}`;const x=await fetch("https://api.groq.com/openai/v1/chat/completions",{method:"POST",headers:{"Authorization":"Bearer "+GROQ,"Content-Type":"application/json"},body:JSON.stringify({model:"llama-3.3-70b-versatile",temperature:0,response_format:{type:"json_object"},messages:[{role:"system",content:"Return only JSON."},{role:"user",content:q}]})});if(!x.ok)return[];const j=JSON.parse((await x.json()).choices?.[0]?.message?.content||"{}");return Array.isArray(j.urls)?j.urls:[]}catch{return[]}}
async function probe(site){
 const r=site.url.replace(/\/$/,""), c=new Set(H.map(x=>abs(r,x)).filter(Boolean)), discovery=[];
 for(const p of ["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml"]){
  const u=r+p,d=await get(u,25000); if(d.status===200){for(const x of xmls(d.body,r))c.add(x);for(const x of await ai(r,d.body))if(same(abs(r,x)||"",r))c.add(abs(r,x))}
  discovery.push({url:u,status:d.status});
 }
 const all=[...c];
 const check=async u=>{const d=await get(u,30000);if(d.status===200&&same(d.url,u)&&valid(d.body))return{url:d.url,method:"direct"};if(BW&&[0,403,429,500,502,503,504].includes(d.status)){const b=await browser(u);if(b&&valid(b))return{url:u,method:"cloudflare_browser"}}return null};
 for(let i=0;i<all.length;i+=8){const hits=(await Promise.all(all.slice(i,i+8).map(check))).filter(Boolean);if(hits.length)return{site:site.name,url:hits[0].url,method:hits[0].method,tested:all.length,discovery}}
 return{site:site.name,url:null,method:null,tested:all.length,discovery};
}
const out=[];for(const s of sites)out.push(await probe(s));console.log(JSON.stringify({native_google_xml_only:true,results:out},null,2));