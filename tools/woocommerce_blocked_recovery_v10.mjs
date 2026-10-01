#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";

const TARGETS=[
["Aarna Computers","https://aarnacomputers.com"],
["KC Computers","https://kccomputers.co.in"],
["Cosmic Byte","https://www.thecosmicbyte.com"],
["KRG KART","https://krgkart.com"],
["PC Kumar Infotech","https://pckumar.in"],
["GamesNComps","https://gamesncomps.com"],
["PCHubShop","https://www.pchubshop.com"],
["Theproaudio","https://www.theproaudio.com"],
["SCL Gaming","https://sclgaming.in"],
["ithunt","https://ithunt.in"]
];

const FAMILIES=[
["woocommerce_google_product_feed","/?woocommerce_gpf=google"],
["ctx_feed_webappick","/wp-content/uploads/woo-feed/google.xml"],
["adtribes_product_feed_pro","/wp-content/uploads/woo-product-feed-pro/google.xml"],
["wpfm_product_feed_manager","/wp-content/uploads/wppfm-feeds/Google.xml"],
["webtoffee_product_feed","/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml"],
["codesolz_merchant_feed_booster","/wp-content/uploads/codesolz-feeds/google-products.xml"],
["feedcraft","/wp-json/feedcraft-product-feed/v1/xml"],
["rexfeed","/wp-content/uploads/rex-feed/google.xml"],
["klpsoft","/wp-content/uploads/klp-feeds-xml/google.xml"],
["icopydoc","/wp-content/uploads/feed-xml-0.xml"]
];

const UA="Mozilla/5.0 (compatible; WooCommerceBlockedRecovery/10.1)";
const TIMEOUT=10000, RETRIES=1, RETRY_DELAY=8000, BETWEEN_PROBES=1500;
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const GOOGLE_NS=/https?:\/\/base\.google\.com\/ns\/1\.0/i;

const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);

function validate(body){
 const x=String(body||"");
 if(!x.trim())return{valid:false,reason:"empty"};
 if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return{valid:false,reason:"sitemap"};
 if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x))return{valid:false,reason:"not_xml"};
 if(!GOOGLE_NS.test(x))return{valid:false,reason:"no_google_namespace"};
 const blocks=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
 if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const good=blocks.filter(b=>["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function fetchOnce(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
   "user-agent":UA,
   "accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.5,*/*;q=0.1",
   "accept-language":"en-IN,en;q=0.9"
  }});
  const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,16*1024*1024);
  return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,transport:r.ok?"public_http":"http_error",challenge:CHALLENGE.test(body.slice(0,40000))};
 }catch(e){
  return{status:0,final_url:url,content_type:"",body:"",transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false};
 }finally{clearTimeout(timer)}
}

async function probe(url){
 let last,attempts=0;
 for(let i=0;i<=RETRIES;i++){
  attempts++;
  last=await fetchOnce(url);
  if(!(last.status===403||last.status===429||last.transport==="timeout"))break;
  if(i<RETRIES)await sleep(RETRY_DELAY);
 }
 const validation=last.status===200&&same(last.final_url,url)?validate(last.body):{valid:false,reason:"http_or_redirect"};
 return{url,...last,attempts,validation};
}

async function runTarget(site,root){
 const evidence=[];
 let nativeHit=null;
 let currentPublic200=0,blocked=0,timeouts=0,clean404=0;
 for(let i=0;i<FAMILIES.length;i++){
  const [family,path]=FAMILIES[i],url=new URL(path,root).href;
  const r=await probe(url);
  evidence.push({family,path,...r,body_sample:r.body.slice(0,400)});
  if(r.validation.valid&&same(r.final_url,root)){nativeHit={family,url:r.final_url,validation:r.validation};break;}
  if(r.status===200)currentPublic200++;
  if(r.status===403||r.status===429||r.challenge)blocked++;
  if(r.transport==="timeout")timeouts++;
  if(r.status===404)clean404++;
  if(i<FAMILIES.length-1)await sleep(BETWEEN_PROBES);
 }
 const status=nativeHit?"NATIVE_FEED_VERIFIED":nativeHit===null&&currentPublic200>0?"PUBLIC_REACHABILITY_CHANGED_NO_NATIVE_FEED":(blocked||timeouts)?"TRANSPORT_REMAINING":"CLEAN_NO_HIT";
 return{
  site,root,status,native_hit:nativeHit,current_public_200:currentPublic200,
  response_summary:{probes:evidence.length,http_200:currentPublic200,http_403:evidence.filter(x=>x.status===403).length,http_429:evidence.filter(x=>x.status===429).length,timeouts,clean_404:clean404,challenges:evidence.filter(x=>x.challenge).length},
  family_results:evidence.map(x=>({family:x.family,url:x.url,status:x.status,final_url:x.final_url,content_type:x.content_type,attempts:x.attempts,transport:x.transport,challenge:x.challenge,validation:x.validation,body_sample:x.body_sample}))
 };
}

const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
const outDir="out/woocommerce-blocked-recovery-v10";await mkdir(outDir,{recursive:true});
const results=[];
for(const target of selected)results.push(await runTarget(...target));
const out={
 schema:"woocommerce-blocked-recovery-v10/v1",
 phase:"persistent-transport-blocked-public-recovery",
 target_count:results.length,shard,shards,
 previous_v7_run:"36820461029",
 policy:{public_only:true,one_request_at_a_time_per_target:true,between_probe_delay_ms:BETWEEN_PROBES,retry_403_429_timeout_once:true,no_bypass:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_auth:true,no_random_token_enumeration:true},
 families:FAMILIES.map(([family,path])=>({family,path})),
 results
};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({
 shard,target_count:results.length,
 native_verified:results.filter(x=>x.native_hit).length,
 reachability_changed:results.filter(x=>x.status==="PUBLIC_REACHABILITY_CHANGED_NO_NATIVE_FEED").length,
 transport_remaining:results.filter(x=>x.status==="TRANSPORT_REMAINING").length,
 clean_no_hit:results.filter(x=>x.status==="CLEAN_NO_HIT").length
},null,2));
