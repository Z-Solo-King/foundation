#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";

const TARGETS=[
["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],["Avikaretails","https://avikaretails.com"],
["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],["Network IT Store","https://networkitstore.in"],
["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],["Only SSD","https://onlyssd.com"],
["IT Gadgets Online","https://itgadgetsonline.com"],["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],
["EZPZ Solutions","https://www.ezpzsolutions.in"],["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],
["ithunt","https://ithunt.in"],["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],
["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://www.pchubshop.com"],["SCL Gaming","https://sclgaming.in"],
["Variety Infotech","https://varietyinfotech.com"],["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],
["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],
["Prime ABGB","https://www.primeabgb.com"],["Kryptronix Gaming","https://kryptronix.in"],["NCL Computer","https://nclcomputer.com"]
];

const TIMEOUT=12000,MAX_CANDIDATES=200,UA="Mozilla/5.0 (compatible; WooCommerceXMLDirectRecovery/11.1)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const XML=/\.xml(?:\.gz)?(?:[?#].*)?$/i;
const SIGNAL=/(feed|google|merchant|shopping|woo|gpf|wpfm|webtoffee|adtribes|ctx)/i;

const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);
const abs=(root,raw)=>{try{const u=new URL(raw,root);return same(u.href,root)?u.href:null}catch{return null}};
const decode=s=>String(s||"").replaceAll("&amp;","&").replaceAll("&quot;","\"").replaceAll("&#39;","'");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function native(body){
 const x=String(body||"");
 if(!x.trim())return{valid:false,reason:"empty"};
 if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^\\s*<(?:urlset|sitemapindex)\\b/i.test(x))return{valid:false,reason:"sitemap"};
 if(!/^\\s*(?:<\\?xml\\b|<rss\\b|<feed\\b|<channel\\b)/i.test(x))return{valid:false,reason:"not_xml"};
 if(!x.toLowerCase().includes("http://base.google.com/ns/1.0")&&!x.toLowerCase().includes("https://base.google.com/ns/1.0"))return{valid:false,reason:"no_google_namespace"};
 const blocks=[];
 for(const part of x.split(/<item\\b[^>]*>/i).slice(1)){const end=part.search(/<\\/item>/i);blocks.push(end>=0?part.slice(0,end):part)}
 for(const part of x.split(/<entry\\b[^>]*>/i).slice(1)){const end=part.search(/<\\/entry>/i);blocks.push(end>=0?part.slice(0,end):part)}
 if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const fields=["id","title","link","price"];
 const good=blocks.filter(b=>fields.every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function get(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
   "user-agent":UA,
   "accept":"text/html,application/xml,text/xml,application/rss+xml,*/*;q=0.2",
   "accept-language":"en-IN,en;q=0.9"
  }});
  const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,12000000);
  return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,challenge:CHALLENGE.test(body.slice(0,40000))};
 }catch(e){return{status:0,final_url:url,content_type:"",body:"",challenge:false,error:e?.name==="AbortError"?"timeout":"request_error"}}
 finally{clearTimeout(timer)}
}

function extractAttrUrls(text,base){
 const out=new Set(),s=String(text||"");
 for(const m of s.matchAll(/(?:href|src|data-url|data-href|loc)=["']([^"']+)["']/gi)){
  const u=abs(base,decode(m[1]));
  if(u&&same(u,base)&&(XML.test(u)||SIGNAL.test(u)&&/\.xml(?:[?#].*)?$/i.test(u))&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 return out;
}

function extractAbsoluteUrls(text,base){
 const out=new Set(),s=String(text||"");
 for(const m of s.matchAll(/https?:\\/\\/[^\\s"'<>]+/gi)){
  const u=abs(base,decode(m[0].replace(/[),.;]+$/,"")));
  if(u&&same(u,base)&&XML.test(u)&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 return out;
}

function searchQueries(domain){
 const q=encodeURIComponent("site:"+domain+" (filetype:xml OR inurl:feed OR inurl:merchant OR inurl:google OR inurl:shopping)");
 return[
  "https://www.google.com/search?q="+q+"&num=20",
  "https://www.bing.com/search?q="+q+"&count=20",
  "https://html.duckduckgo.com/html/?q="+q
 ];
}

async function runSite(site,root){
 const c=new Map();
 const add=(url,source)=>{if(url&&same(url,root)&&c.size<MAX_CANDIDATES&&!c.has(url))c.set(url,source)};
 for(const p of ["/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/"]){
  const u=abs(root,p),r=await get(u);
  for(const x of extractAttrUrls(r.body,u))add(x,"current_public_surface");
  if(p==="/robots.txt")for(const line of r.body.split(/\\r?\\n/)){const m=line.match(/^\\s*Sitemap:\\s*(\\S+)/i);if(m&&same(m[1],root))add(m[1],"robots_sitemap")}
  for(const x of extractAbsoluteUrls(r.body,u))add(x,"current_public_surface");
 }
 const home=await get(root);
 for(const x of extractAttrUrls(home.body,root))add(x,"homepage_reference");
 for(const q of searchQueries(host(root))){
  const r=await get(q);
  for(const x of extractAttrUrls(r.body,root))add(x,"search_index");
  for(const x of extractAbsoluteUrls(r.body,root))add(x,"search_index");
 }
 const candidates=[...c.keys()].filter(u=>XML.test(u)||SIGNAL.test(u));
 const results=[];
 for(let i=0;i<candidates.length;i+=10){
  const batch=await Promise.all(candidates.slice(i,i+10).map(async u=>{
   const r=await get(u);
   const validation=r.status===200&&same(r.final_url,root)?native(r.body):{valid:false,reason:"http_or_redirect"};
   return{url:u,source:c.get(u),status:r.status,final_url:r.final_url,content_type:r.content_type,challenge:r.challenge,validation};
  }));
  results.push(...batch);
 }
 const hits=results.filter(x=>x.validation.valid);
 return{
  site,root,candidate_count:c.size,
  native_urls:[...new Set(hits.map(x=>x.final_url))],
  hits:hits.slice(0,20),
  summary:{candidate_xml:candidates.length,http_200:results.filter(x=>x.status===200).length,http_403:results.filter(x=>x.status===403).length,http_404:results.filter(x=>x.status===404).length,timeouts:results.filter(x=>x.status===0).length,challenges:results.filter(x=>x.challenge).length},
  status:hits.length?"NATIVE_FEED_VERIFIED":"NO_NATIVE_FEED_VERIFIED"
 };
}

const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
const outDir="out/woocommerce-xml-direct-v11";await mkdir(outDir,{recursive:true});
const results=[];for(const t of selected)results.push(await runSite(...t));
const out={schema:"woocommerce-xml-direct-v11/v2",target_count:results.length,shard,shards,policy:{xml_only:true,public_only:true,no_store_api:true,no_product_extraction:true,no_plugin_extraction:true,no_browser:true,no_auth:true,no_bypass:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true},results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.native_urls.length).length,native_urls:results.flatMap(x=>x.native_urls)},null,2));
