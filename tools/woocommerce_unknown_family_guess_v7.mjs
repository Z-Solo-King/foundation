#!/usr/bin/env node
import {mkdir,writeFile} from "node:fs/promises";
import {gunzipSync} from "node:zlib";
const TARGETS=[
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["EZPZ Solutions","https://www.ezpzsolutions.in"],
["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],["ithunt","https://ithunt.in"],["KC Computers","https://kccomputers.co.in"],
["KRG KART","https://krgkart.com"],["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://www.pchubshop.com"],["SCL Gaming","https://sclgaming.in"],
["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],
["Theproaudio","https://www.theproaudio.com"],["Variety Infotech","https://varietyinfotech.com"]];
const UA="Mozilla/5.0 (compatible; WooCommerceUnknownFamilyGuess/7.1)",TIMEOUT=8000,RETRIES=2,RETRY_DELAYS=[2500,6000],CONCURRENCY=2,MAX_EXPANSION=24;
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const GOOGLE_NS=/https?:\/\/base\.google\.com\/ns\/1\.0/i;
const F={
woocommerce_google_product_feed:{representative:"/?woocommerce_gpf=google",expand:["/woocommerce_gpf/google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000"]},
ctx_feed_webappick:{representative:"/wp-content/uploads/woo-feed/google.xml",expand:["/wp-content/uploads/woo-feed/google-shopping.xml","/wp-content/uploads/woo-feed/google-shopping-feed.xml","/wp-content/uploads/woo-feed/google-products.xml","/wp-content/uploads/woo-feed/google-product-feed.xml","/wp-content/uploads/woo-feed/google_merchant.xml","/wp-content/uploads/woo-feed/google-merchant.xml","/wp-content/uploads/woo-feed/merchantcenter2.xml","/wp-content/uploads/woo-feed/listings07.xml","/wp-content/uploads/woo-feed/xml/google.xml","/?woo_feed=google&wt=xml","/?woo_feed=google-shopping&wt=xml"]},
adtribes_product_feed_pro:{representative:"/wp-content/uploads/woo-product-feed-pro/google.xml",expand:["/wp-content/uploads/woo-product-feed-pro/google-shopping.xml","/wp-content/uploads/woo-product-feed-pro/google-products.xml","/wp-content/uploads/woo-product-feed-pro/google-product-feed.xml","/wp-content/uploads/woo-product-feed-pro/Google.xml","/wp-content/uploads/woo-product-feed-pro/feed.xml"]},
wpfm_product_feed_manager:{representative:"/wp-content/uploads/wppfm-feeds/Google.xml",expand:["/wp-content/uploads/wppfm-feeds/Google-Products.xml","/wp-content/uploads/wppfm-feeds/Google-Products-New.xml","/wp-content/uploads/wppfm-feeds/Google-Feed.xml","/wp-content/uploads/wppfm-feeds/GoogleFeed.xml","/wp-content/uploads/wppfm-feeds/Google-Shopping.xml","/wp-content/uploads/wppfm-feeds/google-feed.xml","/wp-content/uploads/wppfm-feeds/feed-google.xml"]},
webtoffee_product_feed:{representative:"/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",expand:["/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_gmc_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_products_Feed.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml","/wp-content/uploads/webtoffee_product_feed/google.xml"]},
codesolz_merchant_feed_booster:{representative:"/wp-content/uploads/codesolz-feeds/google-products.xml",expand:["/wp-content/uploads/codesolz-feeds/google.xml","/wp-content/uploads/codesolz-feeds/google-shopping.xml","/wp-content/uploads/codesolz-feeds/google-feed.xml","/wp-content/uploads/codesolz-feeds/merchant.xml","/wp-content/uploads/codesolz-feeds/feed.xml"]},
feedcraft:{representative:"/wp-json/feedcraft-product-feed/v1/xml",expand:["/wp-json/feedcraft-product-feed/v1/google.xml","/wp-json/feedcraft-product-feed/v1/feed.xml","/wp-json/feedcraft-product-feed/v1/google","/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml","/wp-json/woo-feed/v1/google.xml"]},
rexfeed:{representative:"/wp-content/uploads/rex-feed/google.xml",expand:["/wp-content/uploads/rex-feed/feed.xml","/wp-content/uploads/rex-feed/google-shopping.xml","/wp-content/uploads/rex-feed/google-products.xml","/wp-content/uploads/rex-feed/google-product-feed.xml","/wp-content/uploads/rex-feed/google-shopping-feed.xml","/wp-content/uploads/rex-feed/merchant.xml","/wp-content/uploads/rex-feed/merchant-feed.xml"]},
klpsoft:{representative:"/wp-content/uploads/klp-feeds-xml/google.xml",expand:["/wp-content/uploads/klp-feeds-xml/google-feed.xml","/wp-content/uploads/klp-feeds-xml/google-products.xml","/wp-content/uploads/klp-feeds-xml/google-product-feed.xml","/wp-content/uploads/klp-feeds-xml/google-shopping.xml","/wp-content/uploads/klp-feeds-xml/merchant.xml","/wp-content/uploads/klp-feeds-xml/feed.xml"]},
icopydoc:{representative:"/wp-content/uploads/feed-xml-0.xml",expand:["/wp-content/uploads/feed-xml.xml","/wp-content/uploads/google-feed.xml","/wp-content/uploads/google-products.xml","/wp-content/uploads/google-shopping.xml"]}};
function host(u){try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}}
function sameHost(a,b){return host(a)!==""&&host(a)===host(b)}
function abs(root,p){try{const u=new URL(p,root);if(!/^https?:$/.test(u.protocol)||!sameHost(u.href,root))return null;u.hash="";return u.href}catch{return null}}
function native(body){
 const x=String(body||"");if(!x.trim())return{valid:false,reason:"empty"};if(CHALLENGE.test(x.slice(0,40000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return{valid:false,reason:"sitemap"};if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x))return{valid:false,reason:"not_xml"};if(!GOOGLE_NS.test(x))return{valid:false,reason:"no_google_namespace"};
 const blocks=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);if(!blocks.length)return{valid:false,reason:"no_item_or_entry"};
 const good=blocks.filter(b=>["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b))).length;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
async function fetchOnce(url){
 const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
 try{const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.5,*/*;q=0.1","accept-language":"en-IN,en;q=0.9"}});
 let b=Buffer.from(await r.arrayBuffer());if(b[0]===31&&b[1]===139){try{b=gunzipSync(b)}catch{}}
 const body=b.toString("utf8").slice(0,16*1024*1024);return{status:r.status,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,transport:r.ok?"public_http":"http_error",challenge:CHALLENGE.test(body.slice(0,40000))};
 }catch(e){return{status:0,final_url:url,content_type:"",body:"",transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false}}finally{clearTimeout(timer)}}
async function probe(url){
 let last,attempts=0;for(let i=0;i<=RETRIES;i++){attempts++;last=await fetchOnce(url);if(!(last.status===403||last.status===429||last.transport==="timeout"))break;if(i<RETRIES)await sleep(RETRY_DELAYS[i])}
 const validation=last.status===200&&sameHost(last.final_url,url)?native(last.body):{valid:false,reason:"http_or_redirect"};
 const content_useful=last.status===200&&!last.challenge&&(validation.reason!=="not_xml"||/xml|rss|atom/i.test(last.content_type));
 return{...last,attempts,validation,content_useful};
}
async function mapLimit(rows,limit,fn){const out=new Array(rows.length);let next=0;async function worker(){for(;;){const i=next++;if(i>=rows.length)return;out[i]=await fn(rows[i])}}await Promise.all(Array.from({length:Math.min(limit,rows.length||1)},worker));return out}
async function runSite(site,root){
 const rows=[];
 for(const [family,def] of Object.entries(F)){const representative=abs(root,def.representative),r=await probe(representative);rows.push({family,stage:"representative",candidate:representative,...r});
  if(r.status===200&&!r.challenge&&r.content_useful&&!r.validation.valid){const ex=[...new Set(def.expand.map(x=>abs(root,x)).filter(Boolean))].slice(0,MAX_EXPANSION);const er=await mapLimit(ex,CONCURRENCY,probe);rows.push(...er.map(x=>({...x,family,stage:"family_expansion",candidate:x.final_url})))}
 }
 const hits=rows.filter(x=>x.validation?.valid&&sameHost(x.final_url,root)),limited=rows.some(x=>x.status===403||x.status===429||x.transport==="timeout"||x.challenge);
 return{site,root,status:hits.length?"NATIVE_FEED_VERIFIED":limited?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED",native_hits:hits.slice(0,20),positive_urls:[...new Set(hits.map(x=>x.final_url))],family_useful:[...new Set(rows.filter(x=>x.stage==="representative"&&x.content_useful).map(x=>x.family))],family_transport_blocked:[...new Set(rows.filter(x=>x.stage==="representative"&&(x.status===403||x.status===429||x.transport==="timeout"||x.challenge)).map(x=>x.family))],response_summary:{representatives:rows.filter(x=>x.stage==="representative").length,expansions:rows.filter(x=>x.stage==="family_expansion").length,http_200:rows.filter(x=>x.status===200).length,http_403:rows.filter(x=>x.status===403).length,http_429:rows.filter(x=>x.status===429).length,timeouts:rows.filter(x=>x.transport==="timeout").length,challenges:rows.filter(x=>x.challenge).length},evidence:rows};
}
const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||6),selected=TARGETS.filter((_,i)=>i%shards+1===shard),outDir="out/woocommerce-unknown-family-guess-v7";
await mkdir(outDir,{recursive:true});const results=await Promise.all(selected.map(([site,root])=>runSite(site,root)));
const payload={schema:"woocommerce-unknown-family-guess-v7/v2",phase:"transport-aware-family-evidence",target_count:results.length,shard,shards,policy:{public_only:true,no_store_api:true,no_product_extraction:true,no_plugin_extraction:true,no_browser:true,no_auth:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true,native_acceptance:"current_same_host_google_merchant_xml_payload"},family_strategy:"one representative endpoint per researched family; expand only stable useful 200 responses; retry 403/429/timeouts independently with delay",results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(payload,null,2)+"\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.native_hits.length).length,transport_limited:results.filter(x=>x.status.endsWith("TRANSPORT_LIMITED")).length,clean_no_hit:results.filter(x=>x.status==="NO_NATIVE_FEED_VERIFIED").length},null,2));
