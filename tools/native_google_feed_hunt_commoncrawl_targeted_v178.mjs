#!/usr/bin/env node
const sites=JSON.parse(process.env.SITES_JSON||"[]");
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}catch{return false}};
const nativeText=s=>{const t=String(s||"");return /^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(t)&&/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(t)&&/<item\b/i.test(t)&&/<g:id\b/i.test(t)&&/<g:title\b/i.test(t)&&/<g:link\b/i.test(t)&&/<g:price\b/i.test(t)&&/<g:availability\b/i.test(t)&&!/just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(t)};
async function get(url,ms=25000){const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),ms);try{const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedTargetedCC/2026.09)","Accept":"application/xml,application/rss+xml,text/html,*/*;q=.2"}});return{status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body:await r.text()}}catch(e){return{status:0,url,error:String(e?.name||e)}}finally{clearTimeout(tm)}}
async function cc(q){const r=await get(q,40000);if(r.status!==200)return{ok:false,status:r.status,error:r.body?.slice(0,240)};const rows=[];for(const line of r.body.split(/\r?\n/)){if(!line.trim())continue;try{rows.push(JSON.parse(line))}catch{}}return{ok:true,status:200,rows}}
async function live(u){const d=await get(u,20000);return d.status===200&&same(d.url,u)&&nativeText(d.body)?{ok:true,status:d.status,final:d.url,ct:d.ct,len:d.body.length}:{ok:false,status:d.status,final:d.url,ct:d.ct,len:d.body?.length||0}}
async function indices(){const r=await get("https://index.commoncrawl.org/collinfo.json",25000);if(r.status!==200)throw new Error("collinfo "+r.status);const a=JSON.parse(r.body);return a.slice(0,3).map(x=>x.id)}
async function probe(s,idxs){const root=s.url.replace(//$/,"");const pats=[
 root+"/wp-content/uploads/woo-feed/*",
 root+"/wp-content/uploads/woo-feed/google/*",
 root+"/wp-content/uploads/wppfm-feeds/*",
 root+"/*woocommerce_gpf*",
 root+"/*woo_feed=*",
 root+"/*google*xml*",
 root+"/*merchant*xml*",
 root+"/*product*feed*xml*"
 ];const candidates=new Set(),sources=[];for(const idx of idxs){for(const pat of pats){const q=new URL("https://index.commoncrawl.org/"+idx+"-index");q.searchParams.set("url",pat);q.searchParams.set("output","json");q.searchParams.set("filter","status:200");q.searchParams.set("collapse","urlkey");q.searchParams.set("limit","200");const r=await cc(q.href);sources.push({index:idx,pattern:pat.replace(root,""),ok:r.ok,status:r.status,rows:r.rows?.length||0,error:r.error||null});if(r.ok)for(const row of r.rows||[]){const u=row.url;if(u&&same(u,root)&&/\.xml(?:\.gz)?(?:$|[?#])/i.test(u)&&/google|merchant|shopping|feed|woo|wppfm|ctx/i.test(u))candidates.add(u)}await sleep(350)}}const evidence=[];for(const u of candidates){const v=await live(u);evidence.push({url:u,ok:v.ok,status:v.status,final:v.final,ct:v.ct,len:v.len});if(v.ok)return{site:s.name,url:u,method:"targeted_commoncrawl_live_validation",tested:evidence.length,candidates:candidates.size,indices,sources,evidence:evidence.slice(-20)}}return{site:s.name,url:null,method:null,tested:evidence.length,candidates:candidates.size,indices,sources,evidence:evidence.slice(-30)}}
(async()=>{const idxs=await indices();const results=[];for(const s of sites)results.push(await probe(s,idxs));console.log(JSON.stringify({native_google_xml_only:true,source:"targeted_commoncrawl_feed_patterns+live_validation",indices:idxs,results},null,2))})().catch(e=>{console.error(e.stack||e);process.exitCode=1})