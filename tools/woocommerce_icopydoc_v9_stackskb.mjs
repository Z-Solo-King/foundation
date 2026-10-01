#!/usr/bin/env node
const ROOT="https://stackskb.com";
const PATHS=["/wp-content/uploads/feed-xml-0.xml","/wp-content/uploads/feed-xml-1.xml","/wp-content/uploads/feed-xml-2.xml"];
const UA="Mozilla/5.0 (compatible; WooCommerceIcopyDocRecovery/9.0)";
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const NS=/https?:\/\/base\.google\.com\/ns\/1\.0/i;
function same(a,b){return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}
function validate(x){
 if(!x.trim())return{valid:false,reason:"empty"};
 if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge"};
 if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return{valid:false,reason:"sitemap"};
 if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x))return{valid:false,reason:"not_xml"};
 if(!NS.test(x))return{valid:false,reason:"no_google_namespace"};
 const items=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
 const good=items.filter(b=>["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:items.length,valid_items:good}
}
async function probe(path){
 const url=ROOT+path; const ac=new AbortController(),t=setTimeout(()=>ac.abort(),10000);
 try{const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.5"}});const b=(await r.arrayBuffer());const body=Buffer.from(b).toString("utf8").slice(0,16*1024*1024);return{url,status:r.status,final_url:r.url,content_type:r.headers.get("content-type")||"",same_host:same(r.url,url),validation:r.status===200&&same(r.url,url)?validate(body):{valid:false,reason:"http_or_redirect"},sample:body.slice(0,500)}}
 catch(e){return{url,status:0,final_url:url,content_type:"",same_host:true,validation:{valid:false,reason:e?.name==="AbortError"?"timeout":"request_error"},sample:""}}
 finally{clearTimeout(t)}}
const results=[];for(const p of PATHS)results.push(await probe(p));
const out={schema:"woocommerce-icopydoc-v9/v1",target:"StacksKB",family:"iCopyDoc",policy:{documented_feed_indices_only:true,no_random_token_enumeration:true,no_browser:true,no_auth:true,no_bypass:true},results,native_verified:results.filter(x=>x.validation.valid).map(x=>x.final_url)};
console.log(JSON.stringify(out,null,2));
