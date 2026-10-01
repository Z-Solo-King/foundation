#!/usr/bin/env node
const ROOT="https://stackskb.com";
const PATHS=[
  "/wp-content/uploads/feed-xml-0.xml",
  "/wp-content/uploads/feed-xml-1.xml",
  "/wp-content/uploads/feed-xml-2.xml"
];
const UA="Mozilla/5.0 (compatible; WooCommerceIcopyDocRecovery/9.1)";
const TIMEOUT=10000;
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const GOOGLE_NS=/https?:\/\/base\.google\.com\/ns\/1\.0/i;
const host=u=>{try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}};
const same=(a,b)=>host(a)!==""&&host(a)===host(b);
function validate(body){
  const x=String(body||"");
  if(!x.trim())return{valid:false,reason:"empty"};
  if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
  if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return{valid:false,reason:"sitemap"};
  if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x))return{valid:false,reason:"not_xml"};
  if(!GOOGLE_NS.test(x))return{valid:false,reason:"no_google_namespace"};
  const blocks=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
  if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
  const good=blocks.filter(b=>["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))).length;
  return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}
async function probe(path){
  const url=ROOT+path;
  const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
  try{
    const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{
      "user-agent":UA,
      "accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.5,*/*;q=0.1",
      "accept-language":"en-IN,en;q=0.9"
    }});
    const body=Buffer.from(await r.arrayBuffer()).toString("utf8").slice(0,16*1024*1024);
    return{url,status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",same_host:same(r.url||url,url),validation:r.status===200&&same(r.url||url,url)?validate(body):{valid:false,reason:"http_or_redirect"},sample:body.slice(0,500)};
  }catch(e){
    return{url,status:0,final_url:url,content_type:"",same_host:true,validation:{valid:false,reason:e?.name==="AbortError"?"timeout":"request_error"},sample:""};
  }finally{clearTimeout(timer)}
}
const results=[];
for(const path of PATHS)results.push(await probe(path));
const out={
  schema:"woocommerce-icopydoc-v9/v2",
  target:"StacksKB",
  family:"iCopyDoc",
  policy:{documented_feed_indices_only:true,no_random_token_enumeration:true,no_browser:true,no_auth:true,no_bypass:true},
  results,
  native_verified:results.filter(x=>x.validation.valid).map(x=>x.final_url)
};
console.log(JSON.stringify(out,null,2));
