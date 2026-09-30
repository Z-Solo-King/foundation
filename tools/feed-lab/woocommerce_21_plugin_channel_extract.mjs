#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";
import { URL } from "node:url";

const TARGETS = [
  ["AULA India","https://aulaindia.com"],
  ["Aarna Computers","https://aarnacomputers.com"],
  ["Ads Store","https://adsstore.in"],
  ["Cosmic Byte","https://www.thecosmicbyte.com"],
  ["EZPZ Solutions","https://www.ezpzsolutions.in"],
  ["KC Computers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["Kryptronix Gaming","https://kryptronix.in"],
  ["Meckeys","https://www.meckeys.com"],
  ["Moskeys","https://moskeys.com"],
  ["NCL Computer","https://nclcomputer.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["Prime ABGB","https://www.primeabgb.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["StacksKB","https://stackskb.com"],
  ["Theproaudio","https://www.theproaudio.com"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Viper PC","https://viperpc.in"],
  ["hotshiftpc","https://hotshiftpc.com"],
  ["ithunt","https://ithunt.in"],
];

const CHALLENGE = [
  "just a moment","cf-chl-","cf-turnstile","captcha","access denied",
  "attention required","checking your browser","verify you are human",
  "challenge-platform","enable javascript and cookies"
];

const FETCH_UA = "Mozilla/5.0 (compatible; WooCommercePluginEvidence/3.0; +https://github.com/Z-Solo-King/foundation)";
const BROWSER_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36";

const ROUTES = [
  ["wp-json","/wp-json/"],
  ["rest-route-root","/?rest_route=/"],
  ["wp-v2","/wp-json/wp/v2/"],
  ["rest-route-wp-v2","/?rest_route=/wp/v2/"],
  ["wc-v1","/wp-json/wc/v1/"],
  ["wc-v2","/wp-json/wc/v2/"],
  ["wc-v3","/wp-json/wc/v3/"],
  ["rest-wc-v1","/?rest_route=/wc/v1/"],
  ["rest-wc-v2","/?rest_route=/wc/v2/"],
  ["rest-wc-v3","/?rest_route=/wc/v3/"],
  ["robots","/robots.txt"],
  ["readme","/readme.html"],
];

const sleep = ms => new Promise(r=>setTimeout(r,ms));
const challenge = text => CHALLENGE.some(x => String(text||"").slice(0,30000).toLowerCase().includes(x));

function sameOrigin(a,b){
  try{
    const ah=new URL(a).hostname.toLowerCase().replace(/^www\./,"");
    const bh=new URL(b).hostname.toLowerCase().replace(/^www\./,"");
    return ah===bh;
  }catch{return false}
}

function extractPlugins(text){
  const found=new Map();
  const re=/\/wp-content\/plugins\/([^\/?"'#\\]+)(?:\/[^^?"'#\\\s<]*)?(?:[?&]ver=([^"'&\s<]+))?/gi;
  for(const m of String(text||"").matchAll(re)){
    let slug=decodeURIComponent(m[1]).toLowerCase().replace(/[^a-z0-9._-]/g,"");
    if(!slug) continue;
    if(!found.has(slug)) found.set(slug,new Set());
    if(m[2]) found.get(slug).add(m[2]);
  }
  return [...found.entries()].map(([slug,versions])=>({slug,versions:[...versions]}));
}

function namespacesFromBody(body){
  try{
    const j=JSON.parse(body);
    const values=[];
    if(Array.isArray(j?.namespaces)) values.push(...j.namespaces.map(String));
    for(const k of Object.keys(j||{})) if(/woo|feed|google|merchant|product|wc|plugin/i.test(k)) values.push(String(k));
    return [...new Set(values)];
  }catch{return []}
}

function classifyRestNamespaces(ns){
  const families=[];
  for(const x of ns){
    const low=x.toLowerCase();
    if(/wpfm|wppfm/.test(low)) families.push({family:"wpfm_product_feed_manager",source:"rest_namespace",value:x});
    if(/feed|merchant|google|shopping/.test(low)) families.push({family:"feed_related_namespace",source:"rest_namespace",value:x});
    if(/woocommerce/.test(low)) families.push({family:"woocommerce_related_namespace",source:"rest_namespace",value:x});
  }
  return families;
}

async function publicGet(url, timeout=10000){
  const ctl=new AbortController();
  const t=setTimeout(()=>ctl.abort(),timeout);
  try{
    const r=await fetch(url,{redirect:"follow",signal:ctl.signal,headers:{
      "user-agent":FETCH_UA,"accept":"text/html,application/json,text/plain;q=.9,*/*;q=.1"
    }});
    const b=(await r.text()).slice(0,8*1024*1024);
    return {status:r.status,url:r.url||url,body:b,contentType:r.headers.get("content-type")||"",
      server:r.headers.get("server")||"",challenge:challenge(b),transport:"public_http"};
  }catch(e){
    return {status:0,url,body:"",contentType:"",server:"",challenge:false,
      transport:e?.name==="AbortError"?"timeout":"request_error",error:String(e?.message||e)};
  }finally{clearTimeout(t)}
}

async function browserEvidence(root){
  const { chromium } = await import("playwright");
  const browser=await chromium.launch({headless:true,args:["--no-sandbox","--disable-dev-shm-usage"]});
  const context=await browser.newContext({userAgent:BROWSER_UA,locale:"en-IN",viewport:{width:1440,height:900},javaScriptEnabled:true});
  const page=await context.newPage();
  const responseUrls=new Set();
  page.on("response",res=>{
    try{
      const u=res.url();
      if(sameOrigin(u,root)) responseUrls.add(u);
    }catch{}
  });
  let html="",finalUrl=root,status=0,title="";
  try{
    const res=await page.goto(root,{waitUntil:"domcontentloaded",timeout:30000});
    status=res?.status||0; finalUrl=res?.url||root;
    await page.waitForTimeout(2000);
    try{html=await page.content()}catch{}
    try{title=await page.title()}catch{}
    // Trigger common public catalog surfaces; collect only markup/resource URLs, never response bodies.
    for(const suffix of ["/shop/","/store/","/products/"]){
      try{
        const res2=await page.goto(new URL(suffix,root).href,{waitUntil:"domcontentloaded",timeout:12000});
        await page.waitForTimeout(700);
        if(!html){
          try{html=await page.content()}catch{}
        }
        responseUrls.add(res2?.url||new URL(suffix,root).href);
      }catch{}
    }
    // Return to homepage so homepage-XHR evidence remains represented.
    try{await page.goto(root,{waitUntil:"domcontentloaded",timeout:12000})}catch{}
    await page.waitForTimeout(500);
  }catch(e){
    return {status:0,finalUrl:root,title:"",html:"",challenge:false,
      error:String(e?.message||e),resourceUrls:[],pluginResourceUrls:[]};
  }finally{
    await context.close().catch(()=>{});
    await browser.close().catch(()=>{});
  }
  const urls=[...responseUrls].slice(0,500);
  const pluginResourceUrls=urls.filter(u=>/\/wp-content\/plugins\//i.test(u));
  const restResourceUrls=urls.filter(u=>/(\/wp-json\/|[?&]rest_route=)/i.test(u));
  return {status,finalUrl,title,html,challenge:challenge(html),resourceUrls:urls,pluginResourceUrls,restResourceUrls};
}

function familySignals(plugins,namespaces,xhrUrls,html){
  const source=(html+"\n"+xhrUrls.join("\n")).toLowerCase();
  const out=[];
  const add=(family,reason)=>out.push({family,reason});
  if(plugins.some(x=>/^(woo-feed|webappick-product-feed-for-woocommerce|ctx-feed)$/.test(x.slug))) add("ctx_feed_webappick","plugin_asset");
  if(plugins.some(x=>x.slug==="woo-product-feed-pro")) add("adtribes_product_feed_pro","plugin_asset");
  if(plugins.some(x=>x.slug==="woocommerce-google-product-feed")) add("woocommerce_google_product_feed","plugin_asset");
  if(plugins.some(x=>x.slug==="product-feed-manager" || x.slug==="wppfm")) add("wpfm_product_feed_manager","plugin_asset");
  if(namespaces.some(x=>/wpfm|wppfm/i.test(x))) add("wpfm_product_feed_manager","rest_namespace");
  if(/google-listings-and-ads/.test(source)) add("google_for_woocommerce","public_marker");
  if(/woo-product-feed-pro|adtribes/.test(source)) add("adtribes_product_feed_pro","public_marker");
  if(/woocommerce_gpf/.test(source)) add("woocommerce_google_product_feed","public_marker");
  if(/ctxfeed|webappick/.test(source)) add("ctx_feed_webappick","public_marker");
  return [...new Map(out.map(x=>[x.family+"|"+x.reason,x])).values()];
}

async function inspect(name,root){
  const b=await browserEvidence(root);
  const selected=String(b.finalUrl||root).replace(/\/$/,"");
  const bodies=[b.html||""];
  const endpoints=[];
  let ns=[];
  for(const [name2,path] of ROUTES){
    const r=await publicGet(selected+path);
    endpoints.push({endpoint:name2,path,status:r.status,finalUrl:r.url,contentType:r.contentType,
      transport:r.transport,challenge:r.challenge,bytes:r.body.length,server:r.server});
    if(r.status===200 && r.body && !r.challenge && (name2==="wp-json"||name2==="rest-route-root")){
      bodies.push(r.body); ns.push(...namespacesFromBody(r.body));
    }
  }
  const plugins=extractPlugins(bodies.join("\n")+ "\n" + b.pluginResourceUrls.join("\n"));
  const namespaces=[...new Set(ns)];
  const xhrUrls=b.resourceUrls;
  const feedSignals=familySignals(plugins,namespaces,xhrUrls,b.html||"");
  const readmeMeta=[];
  for(const p of plugins.slice(0,30)){
    for(const file of ["readme.txt","README.md"]){
      const r=await publicGet(selected+"/wp-content/plugins/"+encodeURIComponent(p.slug)+"/"+file,6000);
      if(r.status===200 && r.body && !r.challenge){
        const pluginName=(r.body.match(/^Plugin Name:\s*(.+)$/im)||[])[1]||"";
        const stableTag=(r.body.match(/^Stable tag:\s*(.+)$/im)||[])[1]||"";
        if(pluginName||stableTag) readmeMeta.push({slug:p.slug,file,pluginName:pluginName.trim(),stableTag:stableTag.trim()});
        break;
      }
    }
  }
  const wcRoutes=endpoints.filter(x=>/^wc-v[123]|^rest-wc-v[123]/.test(x.endpoint));
  const browserPluginUrls=b.pluginResourceUrls.slice(0,100);
  const browserRestUrls=b.restResourceUrls.slice(0,100);
  const feedLike=plugins.map(x=>x.slug).filter(x=>/(feed|merchant|product-feed|google-product-feed)/i.test(x))
    .filter(x=>!/^(instagram-feed|facebook-for-woocommerce|feedzy-rss-feeds|advanced-ads)$/.test(x));
  return {
    schema_version:"woocommerce-21-plugin-channel-evidence/v1",
    extractor_basis:"V175-derived browser/XHR recovery + public REST/WP-JSON probes",
    site:name,configured_root:root,selected_origin:selected,status:b.status,
    browser:{status:b.status,finalUrl:b.finalUrl,title:b.title,challenge:b.challenge},
    plugin_assets:plugins,feed_like_plugin_assets:feedLike,
    feed_family_signals:feedSignals,readme_metadata:readmeMeta,
    public_api_namespaces:namespaces,rest_namespace_feed_signals:classifyRestNamespaces(namespaces),
    woocommerce_version_route_probes:wcRoutes,
    homepage_xhr:{resource_count:b.resourceUrls.length,plugin_resource_urls:browserPluginUrls,rest_resource_urls:browserRestUrls},
    public_endpoints:endpoints,
    xhr_plugin_signal_urls:browserPluginUrls,
    identity_tokens:[new URL(root).hostname.replace(/^www\./,"").split(".")[0],name.toLowerCase()].slice(0,10),
  };
}

async function main(){
  const arg=k=>{const a=process.argv.indexOf(k);return a>=0?process.argv[a+1]:""};
  const name=arg("--site"),root=arg("--root"),out=arg("--out");
  if(!name||!root||!out) throw new Error("usage: --site <name> --root <url> --out <path>");
  await mkdir(out.split("/").slice(0,-1).join("/")||".",{recursive:true});
  const report=await inspect(name,root);
  await writeFile(out,JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({
    site:name,browser_status:report.browser.status,
    plugin_assets:report.plugin_assets.length,
    feed_signals:report.feed_family_signals,
    wp_namespaces:report.public_api_namespaces.filter(x=>/wpfm|feed|google|merchant|shopping/i.test(x)),
    wc_routes:report.woocommerce_version_route_probes.map(x=>[x.endpoint,x.status])
  },null,2));
}
if(process.argv[1]?.endsWith("woocommerce_21_plugin_channel_extract.mjs")) await main();
