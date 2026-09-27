#!/usr/bin/env node
const url="https://onlyssd.com/woocommerce_gpf/google";
const r=await fetch(url,{redirect:"follow",headers:{"User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedCanary/2026.09)","Accept":"application/xml,application/rss+xml,text/xml,*/*;q=.2"}});
const t=await r.text();
const m=t.match(/xmlns:([A-Za-z_][\w.-]*)\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i);
const p=m?.[1]||"g";
const ok=r.status===200 && /^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(t) && !!m && new RegExp("<"+p+":id\\b","i").test(t) && new RegExp("<"+p+":title\\b","i").test(t) && new RegExp("<"+p+":link\\b","i").test(t) && new RegExp("<"+p+":price\\b","i").test(t) && new RegExp("<"+p+":availability\\b","i").test(t);
if(!ok){console.error(JSON.stringify({ok:false,status:r.status,final:r.url,content_type:r.headers.get("content-type")||"",length:t.length,prefix:t.slice(0,1000)},null,2));process.exit(1)}
console.log(JSON.stringify({ok:true,canonical:url,final:r.url,status:r.status,content_type:r.headers.get("content-type")||"",length:t.length,namespace_prefix:p,item_count:(t.match(/<item\b/gi)||[]).length},null,2));