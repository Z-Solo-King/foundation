#!/usr/bin/env node
const urls=[
"https://onlyssd.com/?woocommerce_gpf=google",
"https://onlyssd.com/woocommerce_gpf/google/",
"https://onlyssd.com/woocommerce_gpf/google/?gpf_start=0&gpf_limit=1000",
"https://onlyssd.com/woocommerce_gpf/google/?gpf_start=0&gpf_limit=5000"
];
async function p(u){const r=await fetch(u,{redirect:"follow",headers:{"User-Agent":"Mozilla/5.0","Accept":"application/xml,application/rss+xml,text/xml,*/*;q=.2"}});const t=await r.text();return {requested:u,status:r.status,final:r.url,ct:r.headers.get("content-type")||"",len:t.length,prefix:t.slice(0,5000)}}
console.log(JSON.stringify(await Promise.all(urls.map(p)),null,2));