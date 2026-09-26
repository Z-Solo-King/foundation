import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { chromium } from "playwright";

const targets = [
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["avikaretails","https://avikaretails.com"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
["GamesNComps","https://gamesncomps.com"],["Geekbees","https://geekbees.in"],["hotshiftpc","https://hotshiftpc.com"],["itgadgetsonline","https://itgadgetsonline.com"],
["ithunt","https://ithunt.in"],["kccomputers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["Kryptronix Gaming","https://kryptronix.in"],
["NCL Computer","https://nclcomputer.com"],["networkitstore","https://networkitstore.in"],["nexusinfosys","https://www.mynexusinfosys.com"],["Only SDD","https://onlyssd.com"],
["PC Kumar Infotech","https://pckumar.in"],["PC Studio","https://www.pcstudio.in"],["PCHubShop","https://www.pchubshop.com"],["Prime ABGB","https://www.primeabgb.com"],
["quickincomputers","https://quickincomputers.com"],["SCL Gaming","https://sclgaming.in"],["solankienterprises","https://solankienterprises.com"],["Variety Infotech","https://varietyinfotech.com"],
["Viper PC","https://viperpc.in"],["AULA India","https://aulaindia.com"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],
["Moskeys","https://moskeys.com"],["Ninja Dog","https://ninjadog.in"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"]
];

const PATHS=[
"/?woocommerce_gpf=google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
"/woocommerce_gpf/google","/index.php?action=woocommerce_gpf&woocommerce_gpf=google","/?woocommerce_gpf=googleinventory",
"/?feed=google","/?feed=google_shopping","/?feed=google_shopping_feed","/?feed=google-product-feed","/?product_feed=google",
"/google.xml","/google_feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml",
"/product-feed.xml","/products-feed.xml","/merchant-feed.xml","/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml",
"/feed/google.xml","/feed/google-shopping.xml","/feed/google-products.xml","/feeds/products.rss","/feed.xml","/rss.xml","/atom.xml","/products.rss","/index.xml",
"/store/feed","/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/feedcraft-product-feed/v1/json",
"/wp-content/uploads/woo-feed/google/xml/","/wp-content/uploads/woo-feed/google/","/wp-content/uploads/woo-feed/xml/",
"/wp-content/uploads/woo-product-feed-pro/xml/","/wp-content/uploads/wppfm-feeds/"
];

const start=Math.max(0,Number.parseInt(process.env.TARGET_START||"0",10)||0);
const count=Math.max(1,Number.parseInt(process.env.TARGET_COUNT||String(targets.length),10)||targets.length);
const selected=targets.slice(start,start+count);
const UA="Mozilla/5.0 (compatible; WooCommerceGoogleHybrid/1.0)";
const TIMEOUT=15000;
await mkdir("out/hybrid/feeds",{recursive:true});

function slug(s){return String(s).toLowerCase().replace(/[^a-z0-9]+/g,"-").replace(/^-+|-+$/g,"").slice(0,70)||"site";}
function challenge(status,text){const x=String(text||"").slice(0,20000).toLowerCase();return [403,429,430,451,503,520,521,522,523,524].includes(status)&&/just a moment|cf-chl|cloudflare|challenge-platform|cf-turnstile|captcha|verify you are human|access denied|request blocked|attention required|checking your browser/.test(x);}
function abs(raw,base){try{const u=new URL(String(raw||"").trim(),base);return /^https?:$/.test(u.protocol)?u.href:"";}catch{return "";}}
function feedish(u){return /(?:google|merchant|shopping|feed|product|wppfm|woo-feed|codesolz|feedcraft)/i.test(u)&&/(?:xml|rss|atom|feed|product|merchant)/i.test(u);}
function googleNs(xml){return /xmlns(?::[A-Za-z_][\w.-]*)?\s*=\s*["']http:\/\/base\.google\.com\/ns\/1\.0["']/i.test(xml);}
function validate(xml,ct=""){const s=String(xml||"");const root=/^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)/i.test(s);const items=[...s.matchAll(/<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi)].map(m=>m[1]);let n=0;for(const b of items){const f=k=>{const m=b.match(new RegExp(`(?:<g:|[A-Za-z_][\\w.-]*:)${k}\\b[^>]*>([\\s\\S]*?)<\\/\\w+:${k}>`,"i"));return m?.[1]?.replace(/<[^>]+>/g,"").trim()||""};const id=/<(?:[A-Za-z_][\\w.-]*:)?id\\b/i.test(b);const title=/<(?:[A-Za-z_][\\w.-]*:)?title\\b/i.test(b);const link=/<(?:[A-Za-z_][\\w.-]*:)?link\\b/i.test(b);const price=/<(?:[A-Za-z_][\\w.-]*:)?price\\b/i.test(b);n+=Number(id)+Number(title)+Number(link)+Number(price);}const cov=n/Math.max(1,items.length*4);return {qualifies:Boolean(root&&googleNs(s)&&items.length&&cov>=.75),item_count:items.length,required_field_coverage:Number(cov.toFixed(4)),content_type:ct};}
async function get(url){const c=new AbortController();const t=setTimeout(()=>c.abort(),TIMEOUT);try{const r=await fetch(url,{redirect:"follow",signal:c.signal,headers:{"User-Agent":UA,"Accept":"application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.5"}});const b=Buffer.from(await r.arrayBuffer());return {status:r.status,finalUrl:r.url,contentType:r.headers.get("content-type")||"",bytes:b.length,text:b.length<60*1024*1024?b.toString("utf8"):"",buffer:b.length<60*1024*1024?b:null};}finally{clearTimeout(t);}}

function extractLinks(html,base){const out=new Set();for(const m of String(html||"").matchAll(/<(?:link|a)\b[^>]*>/gi)){const tag=m[0];const h=(tag.match(/\bhref=["']([^"']+)["']/i)||[])[1];if(h){const u=abs(h,base);if(u&&new URL(u).origin===new URL(base).origin&&feedish(u))out.add(u);}}for(const m of String(html||"").matchAll(/(?:(?:https?:)?\/\/|\/)[:/?#A-Za-z0-9._%~+\-=&]+/g)){const u=abs(m[0],base);if(u&&new URL(u).origin===new URL(base).origin&&feedish(u))out.add(u);}return [...out];}

async function wayback(base){
  const host=new URL(base).hostname;
  const u=`https://web.archive.org/cdx/search/cdx?url=${encodeURIComponent(host+"/*")}&output=json&fl=original,timestamp,statuscode,mimetype&filter=statuscode:200&collapse=urlkey&limit=1000`;
  const r=await get(u);
  if(r.status!==200||!r.text)return {status:r.status,urls:[],error:"wayback_unavailable"};
  try{const d=JSON.parse(r.text);const rows=Array.isArray(d)?d.slice(1):[];const urls=[];for(const row of rows){const original=row?.[0]||"";if(feedish(original)||/\.xml(?:[?#]|$)/i.test(original))urls.push(original);}return {status:r.status,urls:[...new Set(urls)].slice(0,100)};}catch{return {status:r.status,urls:[],error:"wayback_parse_error"};}
}

async function browserDiscover(base){
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({userAgent:UA,locale:"en-IN"});
  const hits=new Map();
  page.on("response",async response=>{
    try{
      const u=response.url();if(new URL(u).origin!==new URL(base).origin)return;
      const ct=(response.headers()["content-type"]||"").toLowerCase();
      if(!(ct.includes("xml")||ct.includes("rss")||ct.includes("atom")||ct.includes("json"))&&!feedish(u))return;
      if(!feedish(u))return;
      hits.set(u,{url:u,status:response.status(),contentType:ct});
    }catch{}
  });
  let status=0,title="";
  try{const r=await page.goto(base,{waitUntil:"domcontentloaded",timeout:30000});status=r?.status()||0;title=await page.title().catch(()=> "");await page.waitForTimeout(5000);}catch{}
  const urls=[...hits.keys()].slice(0,60);const payload=[];
  for(const u of urls){try{const rr=await get(u);payload.push({url:u,status:rr.status,contentType:rr.contentType,bytes:rr.bytes,validation:rr.status===200?validate(rr.text,rr.contentType):null,text:rr.text});}catch{}}
  await browser.close();
  return {status,title,urls:payload};
}

async function scan([name,base]){
  const evidence=[], candidates=new Map(), feeds=[];
  for(const p of ["/","/robots.txt","/wp-json/"]){try{const r=await get(base+p);evidence.push({path:p,status:r.status,contentType:r.contentType,bytes:r.bytes,finalUrl:r.finalUrl,challenge:challenge(r.status,r.text)});if(p==="/"&&r.status===200)for(const u of extractLinks(r.text,r.finalUrl||base))candidates.set(u,"html_link");if(p==="/wp-json/"&&r.status===200)for(const u of extractLinks(r.text,r.finalUrl||base))candidates.set(u,"wp_rest_link");}catch(e){evidence.push({path:p,error:e.name||String(e)});}}
  for(const p of PATHS)candidates.set(new URL(p,base+"/").href,"v175_public_candidate");
  let wb={status:0,urls:[]};try{wb=await wayback(base);for(const u of wb.urls)candidates.set(u,"wayback_historical");}catch{}
  let br={status:0,urls:[]};try{br=await browserDiscover(base);for(const x of br.urls)candidates.set(x.url,"browser_xhr");}catch(e){br={status:0,urls:[],error:e.name||String(e)};}
  let i=0;const list=[...candidates.entries()];const probes=[];
  async function worker(){while(i<list.length){const [url,source]=list[i++];try{const r=await get(url);if(r.status===200&&r.text){const v=validate(r.text,r.contentType);if(v.qualifies){const hash=createHash("sha256").update(r.buffer||Buffer.from(r.text)).digest("hex");const file=`out/hybrid/feeds/${slug(name)}-${hash.slice(0,12)}.xml`;await writeFile(file,r.buffer||Buffer.from(r.text));feeds.push({url,finalUrl:r.finalUrl,source,file,sha256:hash,bytes:r.bytes,...v});probes.push({url,source,status:r.status,classification:"LIVE_VERIFIED",...v,sha256:hash});}else probes.push({url,source,status:r.status,classification:"NO_MATCH",...v});}else if(r.status===401)probes.push({url,source,status:r.status,classification:"AUTH_REQUIRED"});else if(challenge(r.status,r.text))probes.push({url,source,status:r.status,classification:"BLOCKED_OR_CHALLENGED"});else if(r.status===403)probes.push({url,source,status:r.status,classification:"ACCESS_DENIED"});else if(r.status===429)probes.push({url,source,status:r.status,classification:"RATE_LIMITED"});else probes.push({url,source,status:r.status,classification:`HTTP_${r.status}`});}catch(e){probes.push({url,source,classification:e.name==="AbortError"?"TIMEOUT":"ERROR",error:e.name||String(e)});}}}
  await Promise.all(Array.from({length:6},worker));
  const counts={};for(const p of [...evidence,...probes])counts[p.classification||"INFO"]=(counts[p.classification||"INFO"]||0)+1;
  return {name,base,evidence,wayback:wb,browser:{status:br.status,title:br.title,observed:br.urls?.map(x=>({url:x.url,status:x.status,contentType:x.contentType,bytes:x.bytes,validation:x.validation}))||[],error:br.error},candidate_count:list.length,feeds,counts,probes};
}

const results=[];
for(const t of selected){const r=await scan(t);results.push(r);console.log(JSON.stringify({name:r.name,candidates:r.candidate_count,feeds:r.feeds.map(f=>f.url),wayback:r.wayback.urls.length,browser:r.browser.observed.length}));}
const all=results.flatMap(r=>r.feeds.map(f=>({brand:r.name,base:r.base,...f})));
await writeFile("out/hybrid/summary.json",JSON.stringify({generated_at:new Date().toISOString(),target_count:selected.length,live_verified_feeds:all.length,live_verified_sites:new Set(all.map(x=>x.brand)).size,sites:results.map(r=>({brand:r.name,candidate_count:r.candidate_count,feeds:r.feeds.map(f=>f.url),wayback_urls:r.wayback.urls.length,browser_hits:r.browser.observed.length,counts:r.counts}))},null,2)+"\n");
await writeFile("out/hybrid/audit.json",JSON.stringify({generated_at:new Date().toISOString(),targets:selected.length,results,feeds:all},null,2)+"\n");
