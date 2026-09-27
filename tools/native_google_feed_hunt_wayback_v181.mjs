#!/usr/bin/env node
const sites=JSON.parse(process.env.SITES_JSON||"[]");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}catch{return false}};
const native=s=>{const t=String(s||"");return /^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(t)&&/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(t)&&/<item\b/i.test(t)&&/<g:(?:id|title|link|price)\b/i.test(t)&&!/just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser/i.test(t)};
async function get(u,ms=25000){const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),ms);try{const r=await fetch(u,{redirect:"follow",signal:ac.signal,headers:{"User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedWayback/2026.09)","Accept":"application/json,text/plain,application/xml,text/xml,*/*;q=.2"}});return{status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body:await r.text()}}catch(e){return{status:0,error:String(e?.name||e)}}finally{clearTimeout(tm)}}
function candidate(u){return /\.(?:xml|xml\.gz)(?:$|[?#])/i.test(u)&&/(woocommerce_gpf|woo[-_ ]?feed|ctxfeed|wppfm|google|merchant|shopping|product[-_ ]?feed)/i.test(u)}
async function cdx(pattern){
 const url="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(pattern)+"&output=json&fl=original,statuscode,mimetype,timestamp&filter=statuscode:200&collapse=urlkey&from=2018&to=2026&limit=1000";
 const r=await get(url,45000); if(r.status!==200)return{ok:false,status:r.status,error:String(r.body||"").slice(0,240)};
 try{const j=JSON.parse(r.body);const rows=Array.isArray(j)?j.slice(1).map(x=>({original:x[0],status:x[1],mimetype:x[2],timestamp:x[3]})):[];return{ok:true,status:r.status,rows}}catch{return{ok:false,status:r.status,error:"bad_json"}}
}
async function live(u,root){const r=await get(u,20000);return{url:u,status:r.status,final:r.url,ct:r.ct,len:r.body?.length||0,native:r.status===200&&same(r.url,root)&&native(r.body)}}
async function probe(site){
 const root=site.url.replace(/\/$/,"");const patterns=[
  root+"/*woocommerce_gpf*",
  root+"/*woo-feed*",
  root+"/*ctxfeed*",
  root+"/*wppfm*",
  root+"/*google*.xml*",
  root+"/*merchant*.xml*",
  root+"/*shopping*.xml*",
  root+"/*product*feed*.xml*",
  root+"/wp-content/uploads/woo-feed/*",
  root+"/wp-content/uploads/wppfm-feeds/*"
 ];
 const candidates=new Set(),sources=[];for(const p of patterns){const r=await cdx(p);sources.push({pattern:p.replace(root,""),ok:r.ok,status:r.status,rows:r.rows?.length||0,error:r.error||null});if(r.ok)for(const row of r.rows||[])if(row.original&&same(row.original,root)&&candidate(row.original))candidates.add(row.original);await sleep(250)}
 const evidence=[];for(const u of candidates){const r=await live(u,root);evidence.push(r);if(r.native)return{site:site.name,url:r.final,method:"wayback_cdx_live_validation",candidates:candidates.size,sources,evidence:evidence.slice(-25)}}
 return{site:site.name,url:null,method:null,candidates:candidates.size,sources,evidence:evidence.slice(-40)}
}
(async()=>{const out=[];for(const s of sites)out.push(await probe(s));console.log(JSON.stringify({native_google_xml_only:true,source:"internet_archive_cdx+live_validation",results:out},null,2))})().catch(e=>{console.error(e.stack||e);process.exitCode=1})