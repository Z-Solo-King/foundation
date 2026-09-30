#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";
const SITES=[
 ["EZPZ Solutions","https://www.ezpzsolutions.in"],
 ["Aarna Computers","https://aarnacomputers.com"],
 ["StacksKB","https://stackskb.com"],
 ["Viper PC","https://viperpc.in"],
 ["GamesNComps","https://gamesncomps.com"],
 ["Meckeys","https://www.meckeys.com"],
 ["hotshiftpc","https://hotshiftpc.com"]
];
const UA="Mozilla/5.0 (compatible; WooCommerceHistoricalFeedURLRecovery/10.0)";
const TIMEOUT=7000, CONCURRENCY=8;
const CH=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|request blocked/i;
const H=/\.(?:xml|xml\.gz)(?:$|[?#])|(?:google|merchant|shopping|feed|product[-_]?feed|woocommerce_gpf|woo_feed|wpfm|webtoffee|adtribes|feedcraft|rex-feed|klp-feeds|apfw-feed)/i;
const NS="base.google.com/ns/1.0";
function host(u){try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}}
function same(a,b){return host(a)==host(b)&&host(a)!==""}
function abs(root,raw){try{const u=new URL(raw,root);if(!/^https?:$/.test(u.protocol)||!same(u.href,root))return null;u.hash="";return u.href}catch{return null}}
function native(b){const x=String(b||"");if(!x.trim()||CH.test(x.slice(0,40000))||!x.includes(NS)||!/^(?:\s*<\?xml|\s*<rss|\s*<feed|\s*<channel)/i.test(x))return false;const items=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);return items.some(i=>["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(i)))}
async function get(url){const ac=new AbortController(),t=setTimeout(()=>ac.abort(),TIMEOUT);try{const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.5,*/*;q=0.1"}});const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,12*1024*1024);return{status:r.status,final_url:r.url||url,body,content_type:r.headers.get("content-type")||"",challenge:CH.test(body.slice(0,40000)),transport:r.ok?"public_http":"http_error"}}catch(e){return{status:0,final_url:url,body:"",content_type:"",challenge:false,transport:e?.name==="AbortError"?"timeout":"request_error"}}finally{clearTimeout(t)}}
async function cdx(root){const u="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(root.replace(/\/$/,"")+"/*")+"&output=json&fl=original,statuscode,mimetype,timestamp&filter=statuscode:200&collapse=urlkey&limit=1500";const r=await get(u);if(r.status!==200||!r.body)return[];try{const rows=JSON.parse(r.body);return(Array.isArray(rows)?rows.slice(1):[]).map(a=>({url:a?.[0]||"",timestamp:a?.[3]||""})).filter(x=>x.url&&H.test(x.url)).map(x=>({...x,url:abs(root,x.url)})).filter(x=>x.url).slice(0,250)}catch{return[]}}
async function run(site){const [name,root]=site;const refs=await cdx(root);const uniq=[...new Map(refs.map(x=>[x.url,x])).values()].slice(0,250);const results=[];for(let i=0;i<uniq.length;i+=CONCURRENCY){results.push(...await Promise.all(uniq.slice(i,i+CONCURRENCY).map(async h=>{const r=await get(h.url);const ok=r.status===200&&same(r.final_url,root)&&native(r.body);return{...h,...r,verified:ok}})))}const hits=results.filter(x=>x.verified);return{name,root,historical_refs:refs.length,candidate_count:results.length,status:hits.length?"NATIVE_FEED_VERIFIED":results.some(x=>x.status===403||x.status===429||x.challenge||x.transport==="timeout")?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED",positive_urls:hits.map(x=>x.final_url),hits:hits.slice(0,10),summary:{http_200:results.filter(x=>x.status===200).length,http_403:results.filter(x=>x.status===403).length,http_404:results.filter(x=>x.status===404).length,timeouts:results.filter(x=>x.transport==="timeout").length,challenges:results.filter(x=>x.challenge).length}}}
const results=await Promise.all(SITES.map(run));await mkdir("out/woocommerce-historical-feed-url-v10",{recursive:true});await writeFile("out/woocommerce-historical-feed-url-v10/results.json",JSON.stringify({schema:"wc-historical-feed-url-v10/v1",strategy:"wildcard-wayback-feed-url-recovery",results},null,2)+"\n");console.log(JSON.stringify(results.map(x=>({site:x.name,historical_refs:x.historical_refs,candidates:x.candidate_count,status:x.status,positive_urls:x.positive_urls})),null,2));
