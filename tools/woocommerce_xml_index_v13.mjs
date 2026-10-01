#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";

const TARGETS=[
["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],["Avikaretails","https://avikaretails.com"],
["IT Gadgets Online","https://itgadgetsonline.com"],["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],
["Network IT Store","https://networkitstore.in"],["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],
["AULA India","https://aulaindia.com"],["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],
["EZPZ Solutions","https://www.ezpzsolutions.in"],["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],
["ithunt","https://ithunt.in"],["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],
["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://pchubshop.com"],["SCL Gaming","https://sclgaming.in"],
["Variety Infotech","https://varietyinfotech.com"],["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],
["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],
["Prime ABGB","https://www.primeabgb.com"],["Kryptronix Gaming","https://kryptronix.in"],["NCL Computer","https://nclcomputer.com"]
];

const TIMEOUT=12000,MAX=160,UA="Mozilla/5.0 (compatible; WooCommerceXMLIndexRecovery/13.0)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const XML=/\.xml(?:\.gz)?(?:[?#].*)?$/i;
const FEEDISH=/(feed|google|merchant|shopping|gpf|woocommerce_gpf|woo_feed|product[-_ ]?feed|wpfm|webtoffee|adtribes|ctx)/i;
const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);
const sleep=ms=>new Promise(r=>setTimeout(r,ms));

function native(body){
 const x=String(body||""),t=x.trimStart();
 if(!t)return{valid:false,reason:"empty"};
 if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^<(?:urlset|sitemapindex)\b/i.test(t))return{valid:false,reason:"sitemap"};
 if(!(t.startsWith("<?xml")||/^<(?:rss|feed|channel)\b/i.test(t)))return{valid:false,reason:"not_xml"};
 const lx=x.toLowerCase();
 if(!(lx.includes("https://base.google.com/ns/1.0")||lx.includes("http://base.google.com/ns/1.0")))return{valid:false,reason:"no_google_namespace"};
 const blocks=[];
 for(const tag of ["item","entry"]){
  const reOpen=new RegExp("<"+tag+"(?:\\\\s|>)","ig"),reClose=new RegExp("</"+tag+">","ig");
  let m;
  while((m=reOpen.exec(x))!==null){reClose.lastIndex=m.index+m[0].length;const e=reClose.exec(x);if(!e)break;blocks.push(x.slice(m.index+m[0].length,e.index));}
 }
 if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const good=blocks.filter(b=>{const y=b.toLowerCase();return["id","title","link","price"].every(k=>y.includes("<g:"+k+">"))}).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function get(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
   "user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,*/*;q=0.2","accept-language":"en-IN,en;q=0.9"
  }});
  const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,12000000);
  return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,challenge:CHALLENGE.test(body.slice(0,40000))};
 }catch(e){return{status:0,final_url:url,content_type:"",body:"",challenge:false,error:e?.name==="AbortError"?"timeout":"request_error"}}
 finally{clearTimeout(timer)}
}

async function wayback(domain){
 const u="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(domain+"/*")+
 "&output=json&filter=statuscode:200&filter=mimetype:application/xml&collapse=urlkey&fl=original&limit=200";
 const r=await get(u),out=[];
 try{
  const a=JSON.parse(r.body);
  for(const row of Array.isArray(a)?a.slice(1):[]){if(Array.isArray(row)&&row[0])out.push(row[0]);}
 }catch{}
 return out;
}

async function commonCrawlIndex(){
 const r=await get("https://index.commoncrawl.org/collinfo.json");
 try{
  const a=JSON.parse(r.body);
  return Array.isArray(a)&&a[0]?.id?a[0].id:null;
 }catch{return null}
}

async function commoncrawl(domain,index){
 if(!index)return[];
 const url="https://index.commoncrawl.org/"+encodeURIComponent(index)+"-index?url="+encodeURIComponent(domain+"/*")+
 "&output=json&filter=status:200&filter=url:.*\\\\.xml.*&collapse=urlkey&limit=200";
 const r=await get(url),out=[];
 for(const line of r.body.split(/\\r?\\n/)){
  if(!line.trim())continue;
  try{const row=JSON.parse(line);if(row.url)out.push(row.url)}catch{}
 }
 return out;
}

async function runSite(site,root,index){
 const c=new Map(),add=(u,source)=>{try{const v=new URL(u);if(v.protocol!=="https:"&&v.protocol!=="http:")return;if(!same(v.href,root))return;if(c.size<MAX&&!c.has(v.href))c.set(v.href,source)}catch{}};
 for(const u of await wayback(host(root)))add(u,"wayback_cdx_xml");
 for(const u of await commoncrawl(host(root),index))add(u,"commoncrawl_index_xml");
 const refs=[...c.keys()].filter(u=>XML.test(u)||FEEDISH.test(new URL(u).pathname+new URL(u).search));
 const results=[];
 for(const u of refs){
  const r=await get(u),v=r.status===200&&same(r.final_url,u)?native(r.body):{valid:false,reason:"http_or_redirect"};
  results.push({url:u,source:c.get(u),status:r.status,final_url:r.final_url,content_type:r.content_type,challenge:r.challenge,validation:v});
 }
 const hits=results.filter(x=>x.validation.valid);
 return{site,root,index_sources:{wayback:results.filter(x=>x.source==="wayback_cdx_xml").length,commoncrawl:results.filter(x=>x.source==="commoncrawl_index_xml").length},candidate_count:refs.length,native_urls:[...new Set(hits.map(x=>x.final_url))],hits:hits.slice(0,30),result_sample:results.slice(0,60),status:hits.length?"NATIVE_FEED_VERIFIED":"NO_NATIVE_FEED_VERIFIED"};
}

const index=await commonCrawlIndex();
const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
const outDir="out/woocommerce-xml-index-v13";await mkdir(outDir,{recursive:true});
const results=[];for(const t of selected)results.push(await runSite(...t,index));
const out={schema:"woocommerce-xml-index-v13/v1",target_count:results.length,shard,shards,commoncrawl_index:index,policy:{xml_only:true,public_only:true,wayback_exact_xml_only:true,commoncrawl_exact_xml_only:true,current_revalidation_required:true,no_store_api:true,no_product_extraction:true,no_plugin_inference:true,no_browser:true,no_auth:true,no_bypass:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true},results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.native_urls.length).length,native_urls:results.flatMap(x=>x.native_urls)},null,2));
