import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { chromium } from "playwright";

const SITES=[
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["avikaretails","https://avikaretails.com"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
["GamesNComps","https://gamesncomps.com"],["Geekbees","https://geekbees.in"],["hotshiftpc","https://hotshiftpc.com"],["itgadgetsonline","https://itgadgetsonline.com"],
["ithunt","https://ithunt.in"],["kccomputers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["Kryptronix Gaming","https://kryptronix.in"],
["NCL Computer","https://nclcomputer.com"],["networkitstore","https://networkitstore.in"],["nexusinfosys","https://www.mynexusinfosys.com"],["Only SDD","https://onlyssd.com"],
["PC Kumar Infotech","https://pckumar.in"],["PC Studio","https://www.pcstudio.in"],["PCHubShop","https://www.pchubshop.com"],["Prime ABGB","https://www.primeabgb.com"],
["quickincomputers","https://quickincomputers.com"],["SCL Gaming","https://sclgaming.in"],["solankienterprises","https://solankienterprises.com"],["Variety Infotech","https://varietyinfotech.com"],
["Viper PC","https://viperpc.in"],["AULA India","https://aulaindia.com"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],
["Moskeys","https://moskeys.com"],["Ninja Dog","https://ninjadog.in"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"]
];
const PATHS=["/?woocommerce_gpf=google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000","/woocommerce_gpf/google","/index.php?action=woocommerce_gpf&woocommerce_gpf=google","/?feed=google","/?feed=google_shopping","/?feed=google_shopping_feed","/?feed=google-product-feed","/?product_feed=google","/google.xml","/google_feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml","/product-feed.xml","/products-feed.xml","/merchant-feed.xml","/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feed/google.xml","/feed/google-shopping.xml","/feed/google-products.xml","/feed.xml","/rss.xml","/atom.xml","/products.rss","/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/json","/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/wppfm-feeds/"];
const start=Number.parseInt(process.env.TARGET_START||"0",10)||0;const count=Number.parseInt(process.env.TARGET_COUNT||"8",10)||8;const selected=SITES.slice(start,start+count);
await mkdir("out/fast/feeds",{recursive:true});
const UA="Mozilla/5.0 (compatible; WooCommerceGoogleFast/1.0)";
function challenge(status,text){const s=String(text||"").slice(0,10000).toLowerCase();return [403,429,430,451,503,520,521,522,523,524].includes(status)&&/just a moment|cf-chl|cloudflare|challenge-platform|cf-turnstile|captcha|verify you are human|access denied|request blocked|attention required|checking your browser/.test(s);}
function validate(xml,ct=""){const s=String(xml||"");const root=/^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)/i.test(s);const ns=/xmlns(?::[A-Za-z_][\w.-]*)?\s*=\s*["']http:\/\/base\.google\.com\/ns\/1\.0["']/i.test(s);const items=[...s.matchAll(/<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi)].map(m=>m[1]);let n=0;for(const b of items)for(const k of ["id","title","link","price"])if(new RegExp(`<(?:[A-Za-z_][\\w.-]*:)?${k}\\b[^>]*>`,"i").test(b))n++;const cov=n/Math.max(1,items.length*4);return {qualifies:Boolean(root&&ns&&items.length&&cov>=.75),item_count:items.length,required_field_coverage:Number(cov.toFixed(4)),content_type:ct};}
async function get(url){const c=new AbortController();const t=setTimeout(()=>c.abort(),8000);try{const r=await fetch(url,{redirect:"follow",signal:c.signal,headers:{"User-Agent":UA,"Accept":"application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2"}});const b=Buffer.from(await r.arrayBuffer());return {status:r.status,finalUrl:r.url,ct:r.headers.get("content-type")||"",text:b.toString("utf8"),buffer:b,bytes:b.length};}finally{clearTimeout(t);}}
async function history(base){
 try{
  const host=new URL(base).hostname;
  const u=`https://web.archive.org/cdx/search/cdx?url=${encodeURIComponent(host+"/*")}&output=json&fl=original&filter=statuscode:200&collapse=urlkey&limit=300`;
  const r=await get(u);if(r.status!==200)return [];
  const d=JSON.parse(r.text),rows=Array.isArray(d)?d.slice(1):[];
  return [...new Set(rows.map(x=>x?.[0]).filter(u=>typeof u==="string"&&(/^https?:\/\//.test(u))&&(/[.]xml(?:$|[?#])/i.test(u)||/(?:google|merchant|shopping|product-feed|products-feed|feedcraft|codesolz|woo-feed|wppfm-feeds)/i.test(u))&& !/(?:\/product\/|\/product-category\/|\/compare\/|\/comments\/feed\/|\/wp-json\/wp\/v2\/)/i.test(u)))].slice(0,40);
 }catch{return [];}
}
async function browser(base){
 let browser;try{browser=await chromium.launch({headless:true});const p=await browser.newPage({userAgent:UA,locale:"en-IN"});const hits=[];p.on("response",async res=>{try{const u=res.url();if(new URL(u).origin!==new URL(base).origin)return;const ct=(res.headers()["content-type"]||"").toLowerCase();if(!/(xml|rss|atom|json)/.test(ct)&&!/(google|merchant|shopping|feed|product)/i.test(u))return;const body=await res.body();hits.push({url:u,status:res.status(),ct,body:body.toString("utf8")});}catch{}});let status=0,title="";try{const r=await p.goto(base,{waitUntil:"domcontentloaded",timeout:20000});status=r?.status()||0;title=await p.title().catch(()=> "");await p.waitForTimeout(2500);}catch{}await browser.close();return {status,title,hits};}catch(e){try{await browser?.close();}catch{}return {status:0,title:"",hits:[],error:e.name||String(e)};}}
async function scan([name,base]){
 const out={name,base,feeds:[],probes:[],browser:{},history:[]};let home;
 try{home=await get(base+"/");out.home={status:home.status,ct:home.ct,bytes:home.bytes,challenge:challenge(home.status,home.text)};}catch(e){out.home={error:e.name||String(e)};}
 const cand=[...PATHS.map(p=>new URL(p,base+"/").href)];
 if(home?.status===200){for(const m of home.text.matchAll(/(?:href|src)=["']([^"']+)["']/gi)){const u=m[1];if(/google|merchant|shopping|feed|product/i.test(u)){try{const x=new URL(u,home.finalUrl||base);if(x.origin===new URL(base).origin)cand.push(x.href);}catch{}}}}
 const b=await browser(base);out.browser={status:b.status,title:b.title,observed:b.hits.map(h=>({url:h.url,status:h.status,ct:h.ct,bytes:h.body.length,validation:validate(h.body,h.ct)})).slice(0,80)};
 for(const h of b.hits){const v=validate(h.body,h.ct);if(v.qualifies){const hash=createHash("sha256").update(h.body).digest("hex");const file=`out/fast/feeds/${name.toLowerCase().replace(/[^a-z0-9]+/g,"-")}-${hash.slice(0,12)}.xml`;await writeFile(file,h.body);out.feeds.push({url:h.url,finalUrl:h.url,source:"browser_xhr",file,sha256:hash,bytes:h.body.length,...v});}}
 if(out.feeds.length===0){
  let i=0;const urls=[...new Set(cand)];async function worker(){while(i<urls.length&&out.feeds.length===0){const u=urls[i++];try{const r=await get(u);if(r.status===200&&r.text){const v=validate(r.text,r.ct);out.probes.push({url:u,status:r.status,classification:v.qualifies?"LIVE_VERIFIED":"NO_MATCH",...v});if(v.qualifies){const hash=createHash("sha256").update(r.buffer).digest("hex");const file=`out/fast/feeds/${name.toLowerCase().replace(/[^a-z0-9]+/g,"-")}-${hash.slice(0,12)}.xml`;await writeFile(file,r.buffer);out.feeds.push({url:u,finalUrl:r.finalUrl,source:"public_candidate",file,sha256:hash,bytes:r.bytes,...v});}}}else out.probes.push({url:u,status:r.status,classification:challenge(r.status,r.text)?"BLOCKED_OR_CHALLENGED":r.status===401?"AUTH_REQUIRED":r.status===403?"ACCESS_DENIED":r.status===429?"RATE_LIMITED":`HTTP_${r.status}`});}catch(e){out.probes.push({url:u,classification:e.name==="AbortError"?"TIMEOUT":"ERROR"});}}}
  await Promise.all(Array.from({length:12},worker));
 }
 if(out.feeds.length===0){out.history=await history(base);let i=0;async function hw(){while(i<out.history.length&&out.feeds.length===0){const u=out.history[i++];try{const r=await get(u);if(r.status===200){const v=validate(r.text,r.ct);out.probes.push({url:u,status:r.status,classification:v.qualifies?"LIVE_VERIFIED":"HISTORICAL_NO_MATCH",...v});if(v.qualifies){const hash=createHash("sha256").update(r.buffer).digest("hex");const file=`out/fast/feeds/${name.toLowerCase().replace(/[^a-z0-9]+/g,"-")}-${hash.slice(0,12)}.xml`;await writeFile(file,r.buffer);out.feeds.push({url:u,finalUrl:r.finalUrl,source:"historical_url_current_live",file,sha256:hash,bytes:r.bytes,...v});}}}catch{}}}await Promise.all([hw(),hw(),hw(),hw(),hw(),hw()]);}
 return out;
}
const results=[];for(const t of selected){const r=await scan(t);results.push(r);console.log(JSON.stringify({name:r.name,feeds:r.feeds.map(x=>x.url),history:r.history.length,browser:r.browser.observed?.length||0}));}
const all=results.flatMap(r=>r.feeds.map(f=>({brand:r.name,base:r.base,...f})));
await writeFile("out/fast/summary.json",JSON.stringify({generated_at:new Date().toISOString(),target_count:selected.length,live_verified_feeds:all.length,live_verified_sites:new Set(all.map(x=>x.brand)).size,sites:results.map(r=>({brand:r.name,feeds:r.feeds.map(f=>f.url),history_urls:r.history.length,browser_hits:r.browser.observed?.length||0,home:r.home}))},null,2)+"\n");
await writeFile("out/fast/audit.json",JSON.stringify({generated_at:new Date().toISOString(),targets:selected.length,results,feeds:all},null,2)+"\n");
