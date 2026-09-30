#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { gunzipSync } from "node:zlib";

const TARGETS = [
  {site:"PC Studio",root:"https://www.pcstudio.in",family:"woocommerce_google_product_feed",tokens:["pcstudio","pc-studio","pc_studio"]},
  {site:"Quickin Computers",root:"https://quickincomputers.com",family:"ctx_feed_webappick",tokens:["quickin","quickincomputers","quickin-computers"]},
  {site:"Avikaretails",root:"https://avikaretails.com",family:"adtribes_product_feed_pro",tokens:["avikaretails","avika-retails","avika"]},
  {site:"IT Gadgets Online",root:"https://itgadgetsonline.com",family:"wpfm_product_feed_manager",tokens:["itgadgetsonline","it-gadgets-online","itgadgets","itgo"]}
];

const UA="Mozilla/5.0 (compatible; WooCommerceIdentifiedFamilyGuess/5.1)";
const TIMEOUT=7500;
const CHALLENGE=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked/i;
const NS=/https?:\/\/base\.google\.com\/ns\/1\.0/i;

const GPF=["/?woocommerce_gpf=google","/woocommerce_gpf/google"];
const CTX_DIRS=["/wp-content/uploads/woo-feed/","/wp-content/uploads/woo-feed/xml/","/wp-content/uploads/woo-feed/google/","/wp-content/uploads/woo-feed/google/xml/"];
const CTX_NAMES=["google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml","google-product-feed.xml","google_merchant.xml","google-merchant.xml","merchantcenter2.xml","listings07.xml","google_shopping_ctx_1.xml","google_shopping_ctx_1-3.xml","googleshoplb24a.xml","feed.xml"];
const WPFM_DIRS=["/wp-content/uploads/wppfm-feeds/"];
const WPFM_NAMES=["Google.xml","Google-Products.xml","Google-Products-New.xml","Google-Products-1.xml","Google_Products.xml","Google-Feed.xml","Google-Feed_1.xml","GoogleFeed.xml","Google-Shopping.xml","Google-Shopping-Feed.xml","googlefeed.xml","google-feed.xml","google-products-feed.xml","feed-google.xml","feed-google-shopping.xml","feed.xml"];
const ADTRIBES_DIRS=["/wp-content/uploads/woo-product-feed-pro/","/wp-content/uploads/woo-product-feed-pro/xml/"];
const ADTRIBES_NAMES=["google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml","google-product-feed.xml","Google.xml","feed.xml"];

function host(u){try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return ""}}
function sameHost(a,b){return host(a)!==""&&host(a)===host(b)}
function abs(root,raw){try{const u=new URL(String(raw),root);if(!/^https?:$/.test(u.protocol)||!sameHost(u.href,root))return null;u.hash="";return u.href}catch{return null}}
function decode(s){return String(s||"").replaceAll("&amp;","&").replaceAll("&quot;","\"").replaceAll("&#39;","'")}
function native(body){
  const x=String(body||"");
  if(!x.trim())return {valid:false,reason:"empty"};
  if(CHALLENGE.test(x.slice(0,40000)))return {valid:false,reason:"challenge_or_access_denied"};
  if(/^\s*<(?:urlset|sitemapindex)\b/i.test(x))return {valid:false,reason:"sitemap"};
  if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(x))return {valid:false,reason:"not_xml"};
  if(!NS.test(x))return {valid:false,reason:"no_google_namespace"};
  const blocks=[...x.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),...x.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1]);
  if(!blocks.length)return {valid:false,reason:"no_item_or_entry"};
  let good=0;
  for(const b of blocks)if(["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b)))good++;
  return {valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}
async function get(url,attempts=2){
  let last={status:0,url,final_url:url,content_type:"",body:"",transport:"request_error",challenge:false};
  for(let n=1;n<=attempts;n++){
    const ac=new AbortController(),timer=setTimeout(()=>ac.abort(),TIMEOUT);
    try{
      const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"user-agent":UA,"accept":"application/xml,text/xml,application/rss+xml,text/html;q=0.9,*/*;q=0.1","accept-language":"en-IN,en;q=0.9"}});
      let b=Buffer.from(await r.arrayBuffer());
      if(b[0]===31&&b[1]===139){try{b=gunzipSync(b)}catch{}}
      const body=b.toString("utf8").slice(0,16*1024*1024);
      last={status:r.status,url,final_url:r.url||url,content_type:r.headers.get("content-type")||"",body,transport:r.ok?"public_http":"http_error",challenge:CHALLENGE.test(body.slice(0,40000))};
      if(![429,502,503,504].includes(r.status))return last;
    }catch(e){last={status:0,url,final_url:url,content_type:"",body:"",transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false}}
    if(n<attempts)await new Promise(r=>setTimeout(r,n*500));
    clearTimeout(timer);
  }
  return last;
}
function add(m,root,raw,rank,source,family){
  const u=abs(root,raw);if(!u)return;
  const old=m.get(u);if(!old||rank>old.rank)m.set(u,{url:u,rank,source,family});
}
function identityNames(tokens){
  const out=[];
  for(const t of tokens)for(const s of ["google","google-feed","google-products","google-product-feed","google-shopping","google-shopping-feed","merchant-feed","product-feed","feed"]){
    out.push(t+"-"+s+".xml");out.push(t+"_"+s.replaceAll("-","_")+".xml");
  }
  return [...new Set(out)];
}
async function directoryProbe(site,dirs){
  const out=[];
  for(const dir of dirs){
    const u=abs(site.root,dir);const r=await get(u,1);const urls=new Set();
    for(const m of String(r.body||"").matchAll(/(?:href|data-href|data-url)=["']([^"']+)["']/gi)){
      const x=abs(site.root,decode(m[1]));if(x&&sameHost(x,site.root)&&/\.xml(?:\.gz)?(?:[?#].*)?$/i.test(x))urls.add(x);
    }
    for(const m of String(r.body||"").matchAll(/https?:\/\/[^\s"'<>]+/gi)){
      const x=abs(site.root,m[0].replace(/[),.;]+$/,""));if(x&&sameHost(x,site.root)&&/\.xml(?:\.gz)?(?:[?#].*)?$/i.test(x))urls.add(x);
    }
    out.push({dir,status:r.status,challenge:r.challenge,linked_xml:[...urls].slice(0,300)});
  }
  return out;
}
async function wayback(site,patterns){
  const out=new Set();
  for(const pat of patterns){
    const q="https://web.archive.org/cdx/search/cdx?url="+encodeURIComponent(site.root.replace(/\/$/,"")+pat)+"&output=json&fl=original,statuscode,mimetype,timestamp&filter=statuscode:200&collapse=urlkey&limit=300";
    const r=await get(q,1);if(r.status!==200||!r.body)continue;
    try{
      const rows=JSON.parse(r.body);for(const row of Array.isArray(rows)?rows.slice(1):[]){
        const x=abs(site.root,String(row?.[0]||""));if(x&&sameHost(x,site.root)&&/\.xml(?:\.gz)?(?:[?#].*)?$/i.test(x))out.add(JSON.stringify({url:x,timestamp:row?.[3]||""}));
      }
    }catch{}
  }
  return [...out].map(JSON.parse).slice(0,300);
}
function initialCandidates(site){
  const m=new Map();
  if(site.family==="woocommerce_google_product_feed"){
    for(const p of GPF) add(m,site.root,p,300,"gpf-core",site.family);
    for(const s of [0,50,100,200,250,500,1000,2500,5000])for(const l of [50,100,250,500,1000,2500,5000]){
      add(m,site.root,"/?woocommerce_gpf=google&gpf_start="+s+"&gpf_limit="+l,280,"gpf-partial",site.family);
      add(m,site.root,"/woocommerce_gpf/google?gpf_start="+s+"&gpf_limit="+l,270,"gpf-partial-permalink",site.family);
    }
    for(const c of ["INR","USD","GBP","EUR"]){
      add(m,site.root,"/?woocommerce_gpf=google&currency="+c,245,"gpf-currency",site.family);
      add(m,site.root,"/woocommerce_gpf/google?currency="+c,235,"gpf-currency-permalink",site.family);
    }
    for(const c of ["IN","GB","US","AE"]){
      add(m,site.root,"/?woocommerce_gpf=google&pricecountry="+c,220,"gpf-pricecountry",site.family);
      add(m,site.root,"/woocommerce_gpf/google?pricecountry="+c,210,"gpf-pricecountry-permalink",site.family);
    }
  }else{
    const dirs=site.family==="ctx_feed_webappick"?CTX_DIRS:site.family==="adtribes_product_feed_pro"?ADTRIBES_DIRS:WPFM_DIRS;
    const names=site.family==="ctx_feed_webappick"?CTX_NAMES:site.family==="adtribes_product_feed_pro"?ADTRIBES_NAMES:WPFM_NAMES;
    for(const d of dirs)for(const n of names)add(m,site.root,d+n,220,"family-fixed",site.family);
    for(const n of identityNames(site.tokens))for(const d of dirs)add(m,site.root,d+n,130,"identity-semantic",site.family);
    if(site.family==="ctx_feed_webappick"){
      for(const n of ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase","products","product-feed","listings","listings07","merchantcenter2"]){
        add(m,site.root,"/?woo_feed="+n+"&wt=xml",285,"ctx-query",site.family);
        add(m,site.root,"/?woo_feed="+n,270,"ctx-query-no-format",site.family);
      }
    }
  }
  return m;
}
async function runSite(site){
  const m=initialCandidates(site);
  const dirs=site.family==="ctx_feed_webappick"?CTX_DIRS:site.family==="adtribes_product_feed_pro"?ADTRIBES_DIRS:WPFM_DIRS;
  const dirEvidence=site.family==="woocommerce_google_product_feed"?[]:await directoryProbe(site,dirs);
  for(const d of dirEvidence)for(const u of d.linked_xml)add(m,site.root,u,360,"current-directory-index",site.family);
  const histPatterns=site.family==="woocommerce_google_product_feed"?["/?woocommerce_gpf=google*","/woocommerce_gpf/google*"]:site.family==="ctx_feed_webappick"?["/wp-content/uploads/woo-feed/*","/feed/*","/feeds/*"]:site.family==="adtribes_product_feed_pro"?["/wp-content/uploads/woo-product-feed-pro/*","/wp-content/uploads/woo-product-feed-pro/xml/*"]:["/wp-content/uploads/wppfm-feeds/*"];
  const historical=await wayback(site,histPatterns);
  for(const h of historical)add(m,site.root,h.url,340,"wayback-reference",site.family);
  const selected=[...m.values()].sort((a,b)=>b.rank-a.rank||a.url.localeCompare(b.url)).slice(0,300);
  const results=[];
  for(let i=0;i<selected.length;i+=8){
    const batch=await Promise.all(selected.slice(i,i+8).map(async c=>{
      const r=await get(c.url);const v=r.status===200&&sameHost(r.final_url,site.root)?native(r.body):{valid:false,reason:"http_or_redirect"};
      return {...c,status:r.status,final_url:r.final_url,content_type:r.content_type,transport:r.transport,challenge:r.challenge,validation:v};
    }));
    results.push(...batch);
  }
  const hits=results.filter(x=>x.validation.valid&&sameHost(x.final_url,site.root));
  return {
    site:site.site,root:site.root,family:site.family,candidate_count:selected.length,
    candidate_hits:hits.slice(0,20),positive_urls:hits.map(x=>x.final_url),
    directory_evidence:dirEvidence,historical_reference_count:historical.length,historical_references:historical.slice(0,120),
    status:hits.length?"NATIVE_FEED_VERIFIED":results.some(x=>x.status===403||x.status===429||x.transport==="timeout"||x.challenge)?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED",
    transport_summary:{http_200:results.filter(x=>x.status===200).length,http_403:results.filter(x=>x.status===403).length,http_404:results.filter(x=>x.status===404).length,http_429:results.filter(x=>x.status===429).length,timeouts:results.filter(x=>x.transport==="timeout").length,challenges:results.filter(x=>x.challenge).length}
  };
}
const shard=Number(process.env.SHARD||1),shards=Number(process.env.SHARDS||4),outDir="out/woocommerce-identified-family-v5";
const selected=TARGETS.filter((_,i)=>i%shards+1===shard);
await mkdir(outDir,{recursive:true});
const results=[];
for(const site of selected)results.push(await runSite(site));
const payload={schema:"woocommerce-identified-family-guess-v5/v1",phase:"confirmed-standalone-only",strategy:"research-expanded-family-guessing",shard,shards,target_count:results.length,policy:{public_only:true,no_product_api:true,no_plugin_extraction:true,no_playwright:true,no_auth:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_proxy_rotation:true,no_random_token_enumeration:true,historical_non_authoritative:true,native_acceptance:"current_same_host_google_merchant_xml_payload"},results};
await writeFile(outDir+"/shard-"+shard+".json",JSON.stringify(payload,null,2)+"\n");
console.log(JSON.stringify({shard,target_count:results.length,native_verified:results.filter(x=>x.candidate_hits.length).length,positive_urls:results.flatMap(x=>x.positive_urls),historical_refs:results.reduce((n,x)=>n+x.historical_reference_count,0)},null,2));