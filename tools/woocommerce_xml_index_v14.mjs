#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";

const TARGETS=[
["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],["Avikaretails","https://avikaretails.com"],["IT Gadgets Online","https://itgadgetsonline.com"],["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],["Network IT Store","https://networkitstore.in"],["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],["AULA India","https://aulaindia.com"],["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["EZPZ Solutions","https://www.ezpzsolutions.in"],["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],["ithunt","https://ithunt.in"],["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://pchubshop.com"],["SCL Gaming","https://sclgaming.in"],["Variety Infotech","https://varietyinfotech.com"],["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],["Prime ABGB","https://www.primeabgb.com"],["Kryptronix Gaming","https://kryptronix.in"],["NCL Computer","https://nclcomputer.com"]
];

const TIMEOUT=10000,MAX_ARCHIVE_ROWS=500,MAX_CANDIDATES=80,UA="Mozilla/5.0 (compatible; WooCommerceXMLIndexRecovery/14.0)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const XML=/\.xml(?:\.gz)?(?:[?#].*)?$/i;
const FEEDISH=/(feed|google|merchant|shopping|gpf|woocommerce_gpf|woo_feed|product[-_ ]?feed|wpfm|webtoffee|adtribes|ctx)/i;
const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);
const abs=(root,raw)=>{try{const u=new URL(raw,root);return same(u.href,root)?u.href:null}catch{return null}};

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
  const reO=new RegExp("<"+tag+"(?:\\s|>)","ig"),reC=new RegExp("</"+tag+">","ig");let m;
  while((m=reO.exec(x))){reC.lastIndex=m.index+m[0].length;const e=reC.exec(x);if(!e)break;blocks.push(x.slice(m.index+m[0].length,e.index))}
 }
 if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const good=blocks.filter(b=>{const y=b.toLowerCase();return["id","title","link","price"].every(k=>y.includes("<g:"+k+">"))}).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}

async function get(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{
  const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"user-agent":UA,"accept":"text/plain,application/json,application/xml,text/xml,*/*;q=0.2"}});
  return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body:Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,12000000)};
 }catch(e){return{status:0,final_url:url,content_type:"",body:"",error:e?.name==="AbortError"?"timeout":"request_error"}}
 finally{clearTimeout(timer)}
}

function feedLike(u){
 try{const x=new URL(u);return XML.test(x.href)||FEEDISH.test(x.pathname+x.search)}
 catch{return false}
}

async function wayback(domain){
 const url="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(domain+"/*")+"&output=json&filter=statuscode:200&collapse=urlkey&fl=original&limit="+MAX_ARCHIVE_ROWS;
 const r=await get(url),out=[];
 try{const a=JSON.parse(r.body);for(const row of Array.isArray(a)?a.slice(1):[]){if(Array.isArray(row)&&row[0]&&feedLike(row[0]))out.push(row[0])}}catch{}
 return out;
}
async function ccIndex(){
 const r=await get("https://index.commoncrawl.org/collinfo.json");
 try{const a=JSON.parse(r.body);return Array.isArray(a)&&a[0]?.id?a[0].id:null}catch{return null}
}
async function commoncrawl(domain,index){
 if(!index)return[];
 const url="https://index.commoncrawl.org/"+index+"-index?url="+encodeURIComponent(domain+"/*")+"&output=json&filter=status:200&collapse=urlkey&limit="+MAX_ARCHIVE_ROWS;
 const r=await get(url),out=[];
 for(const line of r.body.split(/\r?\n/)){if(!line.trim())continue;try{const x=JSON.parse(line);if(x.url&&feedLike(x.url))out.push(x.url)}catch{}}
 return out;
}

async function runSite(site,root,index){
 const c=new Map(),add=(u,s)=>{const v=abs(root,u);if(v&&feedLike(v)&&c.size<MAX_CANDIDATES&&!c.has(v))c.set(v,s)};
 for(const u of await wayback(host(root)))add(u,"wayback");
 for(const u of await commoncrawl(host(root),index))add(u,"commoncrawl");
 const refs=[...c.keys()],results=[];
 for(const u of refs){
  const r=await get(u);
  const v=r.status===200&&same(r.final_url,root)?native(r.body):{valid:false,reason:"http_or_redirect"};
  results.push({url:u,source:c.get(u),status:r.status,final_url:r.final_url,content_type:r.content_type,validation:v});
 }
 const hits=results.filter(x=>x.validation.valid);
 return{site,root,candidate_count:refs.length,native_urls:[...new Set(hits.map(x=>x.final_url))],hits:hits.slice(0,20),
  status:hits.length?"NATIVE_FEED_VERIFIED":"NO_NATIVE_FEED_VERIFIED",
  summary:{http_200:results.filter(x=>x.status===200).length,http_403:results.filter(x=>x.status===403).length,http_404:results.filter(x=>x.status===404).length,timeouts:results.filter(x=>x.status===0).length,xml_candidates:refs.filter(x=>XML.test(x)).length},
  archive_sources:{wayback:results.filter(x=>x.source==="wayback").length,commoncrawl:results.filter(x=>x.source==="commoncrawl").length}
 }
}

const index=await ccIndex(),shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6);
const selected=TARGETS.filter((_,i)=>i%shards+1===shard),outDir="out/woocommerce-xml-index-v14";await mkdir(outDir,{recursive:true});
const results=[];for(const t of selected)results.push(await runSite(...t,index));
const out={schema:"woocommerce-xml-index-v14/v1",target_count:results.length,shard,shards,commoncrawl_index:index,policy:{xml_only:true,public_only:true,current_revalidation_required:true,no_random_token_enumeration:true,no_store_api:true,no_product_extraction:true,no_plugin_inference:true,no_browser:true,no_auth:true,no_bypass:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true},results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(out,null,2)+"\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.native_urls.length).length,native_urls:results.flatMap(x=>x.native_urls)},null,2));
