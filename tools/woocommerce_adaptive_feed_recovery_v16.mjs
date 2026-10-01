import {mkdir,writeFile} from "node:fs/promises";

const T=[
["PC Studio","https://www.pcstudio.in","gpf"],["Quickin Computers","https://quickincomputers.com","ctx"],["Avikaretails","https://avikaretails.com","adtribes"],["IT Gadgets Online","https://itgadgetsonline.com","wpfm"],
["Geekbees","https://geekbees.in","google"],["Ninja Dog","https://ninjadog.in","google"],["Network IT Store","https://networkitstore.in","google"],["My Nexus Infosys","https://www.mynexusinfosys.com","google"],["Solanki Enterprises","https://solankienterprises.com","google"],["AULA India","https://aulaindia.com","google"],
["Aarna Computers","https://aarnacomputers.com","unknown"],["Ads Store","https://adsstore.in","unknown"],["EZPZ Solutions","https://www.ezpzsolutions.in","unknown"],["GamesNComps","https://gamesncomps.com","unknown"],["hotshiftpc","https://hotshiftpc.com","unknown"],["ithunt","https://ithunt.in","unknown"],["KC Computers","https://kccomputers.co.in","unknown"],["KRG KART","https://krgkart.com","unknown"],["PC Kumar Infotech","https://pckumar.in","unknown"],["PCHubShop","https://www.pchubshop.com","unknown"],["SCL Gaming","https://sclgaming.in","unknown"],["Variety Infotech","https://varietyinfotech.com","google"],["Viper PC","https://viperpc.in","unknown"],["Cosmic Byte","https://www.thecosmicbyte.com","unknown"],["Meckeys","https://www.meckeys.com","unknown"],["StacksKB","https://stackskb.com","unknown"],["Theproaudio","https://www.theproaudio.com","unknown"],["Prime ABGB","https://www.primeabgb.com","gpf"],["Kryptronix Gaming","https://kryptronix.in","webtoffee"],["NCL Computer","https://nclcomputer.com","webtoffee"]
];
const F={
gpf:["/?woocommerce_gpf=google","/woocommerce_gpf/google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250"],
ctx:["/?woo_feed=google&wt=xml","/?woo_feed=google_shopping&wt=xml","/?woo_feed=google-shopping&wt=xml","/wp-content/uploads/woo-feed/xml/google.xml","/wp-content/uploads/woo-feed/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google/xml/google.xml","/wp-content/uploads/woo-feed/google/xml/google-shopping.xml","/wp-content/uploads/woo-feed/google-shopping.xml","/wp-content/uploads/woo-feed/google-shopping-feed.xml","/wp-content/uploads/woo-feed/feed.xml"],
adtribes:["/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml","/wp-content/uploads/woo-product-feed-pro/google.xml","/wp-content/uploads/woo-product-feed-pro/google-shopping.xml","/wp-content/uploads/woo-product-feed-pro/feed.xml"],
wpfm:["/wp-content/uploads/wppfm-feeds/google.xml","/wp-content/uploads/wppfm-feeds/Google.xml","/wp-content/uploads/wppfm-feeds/Google-Products.xml","/wp-content/uploads/wppfm-feeds/Google-Feed.xml","/wp-content/uploads/wppfm-feeds/google-feed.xml","/wp-content/uploads/wppfm-feeds/google-shopping.xml","/wp-content/uploads/wppfm-feeds/google-shopping-feed.xml","/wp-content/uploads/wppfm-feeds/feed.xml"],
webtoffee:["/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml","/wp-content/uploads/webtoffee_product_feed/google.xml","/wp-content/uploads/webtoffee_product_feed/google-shopping.xml","/wp-content/uploads/webtoffee_product_feed/google-shopping-feed.xml","/wp-content/uploads/webtoffee_product_feed/feed.xml"],
google:[],unknown:[]
};
const G=["/google.xml","/google_feed.xml","/google-feed.xml","/google-products.xml","/google-product-feed.xml","/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/merchant.xml","/product-feed.xml","/feed/google.xml","/feeds/google.xml","/feed.xml"];
const DIRS=["/wp-content/uploads/woo-feed/","/wp-content/uploads/woo-feed/xml/","/wp-content/uploads/woo-feed/google/","/wp-content/uploads/woo-feed/google/xml/","/wp-content/uploads/woo-product-feed-pro/","/wp-content/uploads/woo-product-feed-pro/xml/","/wp-content/uploads/wppfm-feeds/","/wp-content/uploads/codesolz-feeds/","/wp-content/uploads/webtoffee_product_feed/"];
const P=["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/wp-json/"];
const BLOCK=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|sorry, you have been blocked|request blocked/i;
const FEEDISH=/(feed|google|merchant|shopping|woo_feed|woocommerce_gpf|wppfm|webtoffee|adtribes|product[-_ ]?feed)/i;
const UA="Mozilla/5.0 (compatible; FoundationAdaptiveFeedRecovery/16.1)";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)&&host(a)===host(b);
const abs=(b,r)=>{try{const u=new URL(String(r||"").trim(),b);if(!/^https?:$/.test(u.protocol)||!same(u.href,b))return null;u.hash="";return u.href}catch{return null}};
const like=u=>{try{const x=new URL(u);return /\.xml(?:\.gz)?(?:[?#].*)?$/i.test(x.href)||FEEDISH.test(x.pathname+x.search)}catch{return false}};
async function get(u,ms=10000){const c=new AbortController(),t=setTimeout(()=>c.abort(),ms);try{const r=await fetch(u,{redirect:"follow",signal:c.signal,headers:{"user-agent":UA,"accept":"text/html,application/xml,text/xml,application/rss+xml,*/*;q=0.1"}});const b=Buffer.from(await r.arrayBuffer());return{status:r.status,final_url:r.url||u,content_type:r.headers.get("content-type")||"",bytes:b.length,body:b.toString("utf8").slice(0,12000000),error:""}}catch(e){return{status:0,final_url:u,content_type:"",bytes:0,body:"",error:e?.name==="AbortError"?"timeout":"request_error"}}finally{clearTimeout(t)}}
function validate(x){const s=String(x||""),h=s.slice(0,60000);if(!h.trim())return{valid:false,reason:"empty"};if(BLOCK.test(h))return{valid:false,reason:"challenge_or_access_denied"};if(/^\s*<(?:urlset|sitemapindex)\b/i.test(h))return{valid:false,reason:"sitemap"};if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(h))return{valid:false,reason:"not_xml"};if(!/(?:https?:)?\/\/base\.google\.com\/ns\/1\.0/i.test(h))return{valid:false,reason:"no_google_namespace"};const blocks=[...[...s.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].map(m=>m[1]),...[...s.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1])];let good=0;for(const b of blocks)if(["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b)))good++;return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good}}
function urls(text,root){const o=new Set(),s=String(text||"");for(const re of [/(?:href|src|data-url|feedUrl|feed_url|product_feed)\s*=\s*["']([^"']+)["']/gi,/\[[^\]]+\]\((https?:\/\/[^)]+)\)/gi,/<loc[^>]*>\s*([^<]+?)\s*<\/loc>/gi,/https?:\/\/[^\s<>"')]+/gi])for(const m of s.matchAll(re)){const u=abs(root,(m[1]??m[0]).replace(/[),.;]+$/,""));if(u&&like(u))o.add(u)}return[...o]}
async function jina(target){const u="https://r.jina.ai/"+target;const r=await fetch(u,{headers:{"user-agent":UA,"accept":"text/plain","x-respond-with":"markdown"}});return{status:r.status,url:u,body:await r.text()}}
async function siteRun([name,root,fam]){
 const pages=[],seed=new Set(),blocked=[];
 for(const p of P){const u=new URL(p,root).href,r=await get(u,7000);pages.push({path:p,status:r.status,final_url:r.final_url,transport:r.error||"public_http",bytes:r.bytes});if(r.status===403||r.status===429||r.error==="timeout")blocked.push(p);for(const u2 of urls(r.body,r.final_url||u))seed.add(u2)}
 const cand=new Map(),add=(u,source,score)=>{const v=abs(root,u);if(v&&like(v)&&(!cand.has(v)||score>cand.get(v).score))cand.set(v,{url:v,source,score})};
 for(const p of F[fam]||[])add(p,"family_endpoint",300);
 for(const p of G) add(p,"generic",100);
 for(const u of seed)add(u,"public_reference",500);
 let checked=[],winner=null;
 for(const c of [...cand.values()].sort((a,b)=>b.score-a.score).slice(0,100)){
  const r=await get(c.url,5000),v=r.status===200&&same(r.final_url,root)?validate(r.body):{valid:false,reason:r.error==="timeout"?"timeout":"http_or_redirect"};
  const row={...c,status:r.status,final_url:r.final_url,transport:r.error||"public_http",validation:v};checked.push(row);
  if(v.valid){winner={mode:"direct",...row};break}
 }
 let jinaEvidence=null;
 if(!winner&&(blocked.length||checked.some(x=>x.status===403||x.transport==="timeout"))){
  await sleep(Number(process.env.JINA_PACE_MS||3200));
  try{
   const jr=await jina(root);const discovered=urls(jr.body,root);
   const all=[...new Set([...discovered,...[...cand.keys()]])].slice(0,60);
   const jchecks=[];
   for(const u of all.slice(0,12)){
    await sleep(Number(process.env.JINA_PACE_MS||3200));
    try{const x=await jina(u),v=validate(x.body);jchecks.push({url:u,status:x.status,validation:v,bytes:x.body.length});if(v.valid){winner={mode:"jina_reader",url:u,status:x.status,validation:v};break}}catch(e){jchecks.push({url:u,error:String(e)})}
   }
   jinaEvidence={root_status:jr.status,root_bytes:jr.body.length,discovered:discovered.slice(0,80),checks:jchecks,winner:winner?.mode==="jina_reader"?winner:null};
  }catch(e){jinaEvidence={error:String(e)}}
 }
 return{site:name,root,family:fam,status:winner?(winner.mode==="direct"?"NATIVE_FEED_VERIFIED":"JINA_OBSERVED_NATIVE_FEED"):(blocked.length?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED"),winner,direct_pages:pages,blocked_pages:blocked,candidate_count:cand.size,checked:checked.slice(-50),jina:jinaEvidence};
}
const outDir="out/woocommerce-adaptive-feed-v16";await mkdir(outDir,{recursive:true});
const results=[];for(const t of T)results.push(await siteRun(t));
const report={schema_version:"woocommerce-adaptive-feed-recovery-v16/v2",generated_at:new Date().toISOString(),target_count:30,corpus:"30-site learning corpus; AULA included; Only SDD/Moskeys excluded",policy:{public_read_only:true,clearance_cookie_replay:false,captcha_bypass:false,stealth_evasion:false,random_token_enumeration:false,deterministic_native_gate:true,secondary_jina_observation:true},results};
await writeFile(outDir+"/woocommerce_adaptive_feed_recovery_v16.json",JSON.stringify(report,null,2)+"\n");
const n=results.filter(x=>x.status==="NATIVE_FEED_VERIFIED"),j=results.filter(x=>x.status==="JINA_OBSERVED_NATIVE_FEED");
console.log(JSON.stringify({target_count:30,native_verified:n.length,native_urls:n.map(x=>x.winner.final_url),jina_observed:j.length,jina_urls:j.map(x=>x.winner.url),transport_limited:results.filter(x=>x.status==="NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED").length},null,2));
