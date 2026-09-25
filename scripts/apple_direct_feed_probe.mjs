import { writeFile } from "node:fs/promises";
const UA="Mozilla/5.0 AppleWebKit/537.36 Chrome/153 Safari/537.36";
const seen=new Set(), out={pages:[],scripts:[],direct:[],errors:[]};
async function get(url,opt={}){const r=await fetch(url,{redirect:"follow",headers:{"user-agent":UA,"accept":"*/*",...(opt.headers||{})},...opt});const t=await r.text();return {url:r.url,status:r.status,ct:r.headers.get("content-type")||"",text:t};}
function paths(t){return [...new Set((t.match(/(?:https?:\\/\\/[^"\'\\s<>]+|\\/[^"\'\\s<>]{2,160})/g)||[]))].filter(x=>/api|shop|product|catalog|commerce|search|fulfill|pricing|inventory|availability|parts|config|model/i.test(x));}
function productish(t){return /(?:partNumber|productNumber|sku|price|finalPrice|productId|modelCode|productName|retailPrice)/i.test(t)&&/(?:json|items|products|parts|product)/i.test(t)}
async function main(){
 for(const u of ["https://www.apple.com/in/shop/buy-iphone/iphone-17","https://www.apple.com/in/shop/buy-iphone/iphone-17-pro","https://www.apple.com/in/shop/buy-iphone"]){
  try{const r=await get(u,{headers:{accept:"text/html"}});out.pages.push({url:u,final:r.url,status:r.status,ct:r.ct,bytes:r.text.length});
   const ss=[...r.text.matchAll(/<script\\b[^>]+src=["\'"]([^"\'"]+)["\'"]/gi)].map(m=>new URL(m[1],r.url).href);
   for(const s of [...new Set(ss)].slice(0,100)){try{const x=await get(s,{headers:{accept:"application/javascript,text/javascript,*/*"}});const h=paths(x.text);if(h.length)out.scripts.push({url:s,status:x.status,bytes:x.text.length,paths:h.slice(0,120),productish:productish(x.text)});}catch(e){out.errors.push({stage:"script",url:s,error:String(e)})}}
  }catch(e){out.errors.push({stage:"page",url:u,error:String(e)})}
 }
 const candidates=[
 "https://www.apple.com/in/shop/fulfillment-messages",
 "https://www.apple.com/in/shop/availability",
 "https://www.apple.com/in/shop/product",
 "https://www.apple.com/in/shop/search-services",
 "https://www.apple.com/in/shop/sba/d/init",
 "https://www.apple.com/in/shop/sba/d",
 "https://www.apple.com/in/shop/api",
 "https://www.apple.com/in/shop/catalog",
 "https://www.apple.com/in/shop/products",
 "https://www.apple.com/in/shop/feed",
 "https://www.apple.com/in/shop/search?query=iphone"
 ];
 for(const u of candidates){try{const r=await get(u);out.direct.push({url:r.url,status:r.status,ct:r.ct,bytes:r.text.length,productish:productish(r.text),sample:r.text.slice(0,2500),paths:paths(r.text).slice(0,60)})}catch(e){out.errors.push({stage:"direct",url:u,error:String(e)})}}
 const all=[...out.scripts.flatMap(x=>x.paths),...out.direct.flatMap(x=>x.paths)];
 out.endpointCandidates=[...new Set(all)].filter(x=>/^\\//.test(x)||/^https?:/i.test(x)).slice(0,500);
 await writeFile("apple-direct-probe.json",JSON.stringify(out,null,2));
 const qs=out.direct.filter(x=>x.productish).map(x=>({url:x.url,status:x.status,ct:x.ct}));
 console.log(JSON.stringify({pages:out.pages,scripts:out.scripts.length,direct:out.direct.length,productishDirect:qs,endpointCandidates:out.endpointCandidates.slice(0,100)},null,2));
} main().catch(async e=>{out.errors.push({stage:"fatal",error:String(e)});await writeFile("apple-direct-probe.json",JSON.stringify(out,null,2));process.exitCode=1});