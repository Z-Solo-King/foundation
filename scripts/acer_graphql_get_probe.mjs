import { execFileSync } from "node:child_process";
const UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";
function curl(args){try{return execFileSync("curl",["--silent","--show-error","--compressed","--connect-timeout","10","--max-time","25","-4","--http1.1","-A",UA,...args],{encoding:"utf8",maxBuffer:12000000})}catch(e){return "ERROR:"+String(e)}}
function out(label,args){const t=curl(args);const line=t.slice(0,12000);console.log(JSON.stringify({label,bytes:t.length,productish:/(sku|name|price_range|products|route|product)/i.test(t),sample:line},null,2));}
const q1=encodeURIComponent("query { route(url: \"en-in/acer-aspire-c27\") { ... on ProductInterface { name sku small_image { url } price_range { minimum_price { final_price { value currency } regular_price { value currency } } } } } }");
out("route-get",["-H","Accept: application/json","-H","Store: default","https://store.acer.com/en-in/graphql?query="+q1]);
const q2=encodeURIComponent("query { products(search: \"laptop\", pageSize: 50, currentPage: 1) { total_count page_info { current_page page_size total_pages } items { sku name url_key } } }");
out("products-get",["-H","Accept: application/json","-H","Store: default","https://store.acer.com/en-in/graphql?query="+q2]);