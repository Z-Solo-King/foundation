#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";

const TARGETS=[
["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],
["Avikaretails","https://avikaretails.com"],["IT Gadgets Online","https://itgadgetsonline.com"],
["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],["Network IT Store","https://networkitstore.in"],
["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],["AULA India","https://aulaindia.com"],
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],["ithunt","https://ithunt.in"],
["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["PC Kumar Infotech","https://pckumar.in"],
["PCHubShop","https://pchubshop.com"],["SCL Gaming","https://sclgaming.in"],["Variety Infotech","https://varietyinfotech.com"],
["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],
["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],["Prime ABGB","https://www.primeabgb.com"],
["Kryptronix Gaming","https://kryptronix.in"],["NCL Computer","https://nclcomputer.com"]
];

const TIMEOUT=10000;
const MAX_CANDIDATES=100;
const UA="Mozilla/5.0 (compatible; WooCommerceXMLDeepRecovery/12.0)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const XML_PATH=/\.xml(?:\.gz)?(?:[?#].*)?$/i;
const FEED_QUERY=/(?:feed|gpf|google|merchant|shopping|woo_feed|woocommerce_gpf|product_feed|wpfm|webtoffee|adtribes|ctx)=/i;
const FEED_PATH=/\/(?:feed|feeds|google|merchant|shopping|gpf|wpfm|webtoffee|adtribes|ctx|product-feed)\b/i;

const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);
const abs=(root,raw)=>{try{const u=new URL(raw,root);return same(u.href,root)?u.href:null}catch{return null}};
const decode=s=>String(s||"").replaceAll("&amp;","&").replaceAll("&quot;","\"").replaceAll("&#39;","'");
const isCandidate=url=>{try{const u=new URL(url);return XML_PATH.test(u.href)||FEED_QUERY.test(u.search)||FEED_PATH.test(u.pathname)}catch{return false}};
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function native(body){
 const x=String(body||"");
 const t=x.trimStart();
 if(!t)return{valid:false,reason:"empty"};
 if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^<(?:urlset|sitemapindex)\b/i.test(t))return{valid:false,reason:"sitemap"};
 if(!(t.startsWith("<?xml")||/^<(?:rss|feed|channel)\b/i.test(t)))return{valid:false,reason:"not_xml"};
 const lx=x.toLowerCase();
 if(!(lx.includes("https://base.google.com/ns/1.0")||lx.includes("http://base.google.com/ns/1.0")))return{valid:false,reason:"no_google_namespace"};
 const blocks=[];
 for(const tag of ["item","entry"]){
  let pos=0;
  const open="<"+tag,close="</"+tag+">";
  while((pos=lx.indexOf(open,pos))>=0){
   const next=lx[pos+open.length];
   if(next&&next!==" "&&next!=="\t"&&next!=="\r"&&next!=="\n"&&next!==">"){pos+=open.length;continue}
   const end=lx.indexOf(close,pos+open.length);
   if(end<0)break;
   blocks.push(x.slice(pos+open.length,end));pos=end+close.length;
  }
 }
 if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const good=blocks.filter(b=>{const y=b.toLowerCase();return["id","title","link","price"].every(k=>y.includes("<g:"+k+">"))}).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function get(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
   "user-agent":UA,"accept":"text/html,application/xml,text/xml,application/rss+xml,*/*;q=0.2","accept-language":"en-IN,en;q=0.9"
  }});
  const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,12000000);
  return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",link:r.headers.get("link")||"",body,challenge:CHALLENGE.test(body.slice(0,40000))};
 }catch(e){return{status:0,final_url:url,content_type:"",link:"",body:"",challenge:false,error:e?.name==="AbortError"?"timeout":"request_error"}}
 finally{clearTimeout(timer)}
}

function extract(text,base){
 const out=new Set(),s=String(text||"");
 for(const m of s.matchAll(/(?:href|src|data-url|data-href|loc)=["']([^"']+)["']/gi)){
  const u=abs(base,decode(m[1]));if(u&&isCandidate(u)&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 for(const m of s.matchAll(/["'](\/[^"'<>]{1,500})["']/g)){
  const u=abs(base,decode(m[1]));if(u&&isCandidate(u)&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 for(const m of s.matchAll(/https?:\/\/[^\s"'<>]+/gi)){
  const u=abs(base,decode(m[0].replace(/[),.;]+$/,"")));if(u&&isCandidate(u)&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 return out;
}

function searchUrls(text,base){
 const out=extract(text,base);
 for(const m of String(text||"").matchAll(/<a[^>]+href=["']([^"']+)["'][^>]*>/gi)){
  const raw=decode(m[1]);
  for(const key of ["uddg","url","q"]){try{const u=new URL(raw);const v=u.searchParams.get(key);if(v)raw=decode(v)}catch{}}
  const u=abs(base,raw);if(u&&isCandidate(u)&&!u.toLowerCase().includes("sitemap"))out.add(u);
 }
 return out;
}

async function wayback(root){
 const domain=host(root);
 const url="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(domain+"/*")+"&output=json&filter=statuscode:200&filter=mimetype:application/xml&collapse=urlkey&fl=original&limit=40";
 const r=await get(url);
 const out=new Set();
 try{
  const data=JSON.parse(r.body);
  for(const row of Array.isArray(data)?data.slice(1):[])if(typeof row==="string"){}else if(Array.isArray(row)&&row[0]){const u=abs(root,row[0]);if(u&&isCandidate(u))out.add(u)}
 }catch{}
 return out;
}

async function runSite(site,root){
 const candidates=new Map();
 const add=(u,source)=>{if(u&&same(u,root)&&isCandidate(u)&&candidates.size<MAX_CANDIDATES&&!candidates.has(u))candidates.set(u,source)};
 for(const p of ["/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml"]){
  const u=abs(root,p),r=await get(u);
  for(const x of extract(r.body,u))add(x,"current_public_surface");
  for(const x of extract(r.link,u))add(x,"http_link_header");
  if(p==="/robots.txt")for(const line of r.body.split(/\r?\n/)){const m=line.match(/^\s*Sitemap:\s*(\S+)/i);if(m){const u2=abs(root,m[1]);if(u2)add(u2,"robots_sitemap")}}
 }
 const home=await get(root);
 for(const x of extract(home.body,root))add(x,"current_homepage");
 for(const x of extract(home.link,root))add(x,"http_link_header");
 const queries=[
  "site:"+host(root)+" filetype:xml",
  "site:"+host(root)+" \"base.google.com/ns/1.0\"",
  "site:"+host(root)+" \"g:id\" \"g:price\"",
  "site:"+host(root)+" \"woocommerce_gpf=google\"",
  "site:"+host(root)+" \"woo_feed=\"",
  "site:"+host(root)+" \"feed-xml\""
 ];
 for(const q0 of queries){
  const q=encodeURIComponent(q0);
  for(const engine of [
   "https://www.google.com/search?q="+q+"&num=20",
   "https://www.bing.com/search?q="+q+"&count=20",
   "https://html.duckduckgo.com/html/?q="+q
  ]){
   const r=await get(engine);
   for(const x of searchUrls(r.body,engine))add(x,"search_index");
  }
 }
 if(candidates.size<5){
  for(const x of await wayback(root))add(x,"wayback_exact_xml");
 }
 const refs=[...candidates.keys()];
 const results=[];
 for(let i=0;i<refs.length;i+=8){
  const batch=await Promise.all(refs.slice(i,i+8).map(async u=>{
   const r=await get(u);
   const validation=r.status===200&&same(r.final_url,root)?native(r.body):{valid:false,reason:"http_or_redirect"};
   return{url:u,source:candidates.get(u),status:r.status,final_url:r.final_url,content_type:r.content_type,challenge:r.challenge,validation};
  }));
  results.push(...batch);
 }
 const hits=results.filter(x=>x.validation.valid);
 return{
  site,root,candidate_count:refs.length,native_urls:[...new Set(hits.map(x=>x.final_url))],hits:hits.slice(0,20),
  summary:{candidates:refs.length,http_200:results.filter(x=>x.status===200).length,http_403:results.filter(x=>x.status===403).length,http_404:results.filter(x=>x.status===404).length,timeouts:results.filter(x=>x.status===0).length,challenges:results.filter(x=>x.challenge).length},
  status:hits.length?"NATIVE_FEED_VERIFIED":"NO_NATIVE_FEED_VERIFIED"
 };
}

const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
const outDir="out/woocommerce-xml-deep-v12";await mkdir(outDir,{recursive:true});
const results=[];for(const t of selected)results.push(await runSite(...t));
const out={schema:"woocommerce-xml-deep-v12/v1",target_count:results.length,shard,shards,policy:{xml_only:true,public_only:true,no_store_api:true,no_product_extraction:true,no_plugin_inference:true,no_browser:true,no_auth:true,no_bypass:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true},results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.native_urls.length).length,native_urls:results.flatMap(x=>x.native_urls)},null,2));
