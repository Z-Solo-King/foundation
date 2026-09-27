#!/usr/bin/env node
const sites=JSON.parse(process.env.SITES_JSON||"[]");
const CF_TOKEN=process.env.CLOUDFLARE_API_TOKEN||"";
const CF_ACCOUNT=process.env.CLOUDFLARE_ACCOUNT_ID||"";
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const same=(a,b)=>{try{return new URL(a).hostname.replace(/^www\./,"")===new URL(b).hostname.replace(/^www\./,"")}catch{return false}};
const abs=(root,x)=>{try{return new URL(x,root).href}catch{return null}};
const nativeText=s=>{const t=String(s||"");return /^\s*(?:<\?xml[^>]*>\s*)?<rss\b/i.test(t)&&/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(t)&&/<item\b/i.test(t)&&/<g:id\b/i.test(t)&&/<g:title\b/i.test(t)&&/<g:link\b/i.test(t)&&/<g:price\b/i.test(t)&&/<g:availability\b/i.test(t)&&!/just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(t)};
const challenge=s=>/just a moment|cf-chl-|cf-browser-verification|cf-mitigated|turnstile|captcha|access denied|attention required|checking your browser|verify you are human/i.test(String(s||""));
async function http(url,ms=30000){const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),ms);try{const r=await fetch(url,{redirect:"follow",signal:ac.signal,headers:{"User-Agent":"Mozilla/5.0 (compatible; NativeGoogleFeedHunt/2026.09)","Accept":"application/xml,application/rss+xml,text/xml,application/json,text/html;q=.8,*/*;q=.2","Accept-Language":"en-IN,en;q=.9"}});return{status:r.status,url:r.url,ct:r.headers.get("content-type")||"",body:await r.text()}}catch(e){return{status:0,url,error:String(e?.name||e)}}finally{clearTimeout(tm)}}
function discoverUrls(text,root,set){
 for(const m of String(text||"").matchAll(/https?:\/\/[^\s"'<>]+/gi)){const u=m[0].replace(/[),.;]+$/,"");if(same(u,root)&&(/\.xml(?:\.gz)?(?:$|[?#])/i.test(u)||/woocommerce_gpf|woo_feed|ctxfeed|wppfm|google|merchant|shopping|product[-_]feed/i.test(u)))set.add(u)}
 for(const m of String(text||"").matchAll(/(?:href|loc)=["']([^"']+)["']/gi)){const u=abs(root,m[1]);if(u&&same(u,root)&&(/\.xml(?:\.gz)?(?:$|[?#])/i.test(u)||/woocommerce_gpf|woo_feed|ctxfeed|wppfm|google|merchant|shopping|product[-_]feed/i.test(u)))set.add(u)}
}
function discoverNames(obj,out,path=""){
 if(obj&&typeof obj==="object"){for(const [k,v] of Object.entries(obj)){const lk=k.toLowerCase();const p=path+"/"+lk;if(typeof v==="string"){if(/(feed[_-]?url|feed[_-]?file|file[_-]?url|feed[_-]?path|export[_-]?url|xml[_-]?url|url)$/i.test(lk)&&/https?:\/\//i.test(v))out.add(v);if(/(feed[_-]?name|filename|file|name)$/i.test(lk)&&/^[A-Za-z0-9._-]{3,150}$/.test(v))out.add("NAME:"+v)}else discoverNames(v,out,p)}}
}
async function cf(path,body){
 if(!CF_TOKEN||!CF_ACCOUNT)return{ok:false,error:"missing_cloudflare_credentials"};
 const ac=new AbortController(),tm=setTimeout(()=>ac.abort(),65000);
 try{const r=await fetch(`https://api.cloudflare.com/client/v4/accounts/${CF_ACCOUNT}${path}`,{method:"POST",signal:ac.signal,headers:{"Authorization":"Bearer "+CF_TOKEN,"Content-Type":"application/json","Accept":"application/json"},body:JSON.stringify(body)});const text=await r.text();let j=null;try{j=JSON.parse(text)}catch{}return{ok:r.ok,status:r.status,data:j,raw:text.slice(0,1000)}}catch(e){return{ok:false,status:0,error:String(e?.name||e)}}finally{clearTimeout(tm)}
}
async function validate(url){
 const d=await http(url,20000);
 if(d.status===200&&same(d.url,url)&&nativeText(d.body))return{ok:true,method:"direct",url:d.url,status:d.status,ct:d.ct,len:d.body.length};
 if(d.status===200&&nativeText(d.body))return{ok:true,method:"direct",url:d.url,status:d.status,ct:d.ct,len:d.body.length};
 return{ok:false,probe:{status:d.status,final:d.url,ct:d.ct,len:d.body?.length||0,challenge:challenge(d.body)}};
}
async function pluginDiscovery(root,wp){
 const cands=new Set(),signals=[];
 for(const ver of ["v8","v7","v6","v5","v4","v3","v2","v1"]){
   const u=`${root}/wp-json/ctxfeed/${ver}/feeds`;const r=await http(u,12000);
   if(r.status===200&&r.body&&/^[\s\S]*[\[{]/.test(r.body)){signals.push({url:u,status:r.status,ct:r.ct,len:r.body.length});try{const j=JSON.parse(r.body);const raw=new Set();discoverNames(j,raw);for(const x of raw){if(/^NAME:/.test(x)){const n=x.slice(5);for(const pat of [
        `/?woo_feed=${encodeURIComponent(n)}&wt=xml`,
        `/?feed=${encodeURIComponent(n)}`,
        `/wp-content/uploads/woo-feed/google/xml/${encodeURIComponent(n)}.xml`,
        `/wp-content/uploads/woo-feed/xml/${encodeURIComponent(n)}.xml`
      ]){const a=abs(root,pat);if(a)cands.add(a)}}else{const a=abs(root,x);if(a&&same(a,root))cands.add(a)}}}catch{}}
 }
 return{cands:[...cands],signals};
}
async function probe(site){
 const root=site.url.replace(/\/$/,"");const cands=new Set();const browserDiscovered=new Set();const discovery=[];const source=new Map();
 const hist=[
  "/?woocommerce_gpf=google","/woocommerce_gpf/google","/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000","/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
  "/google.xml","/google_feed.xml","/google-feed.xml","/google_base.xml","/google-products.xml","/google-product-feed.xml",
  "/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml","/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml",
  "/gpf.xml","/product-feed.xml","/products-feed.xml","/feed/google.xml","/feed/google-products.xml","/feed/google-product-feed.xml",
  "/feed/google-shopping.xml","/feed/google-shopping-feed.xml","/feed/merchant.xml","/feed/merchant-feed.xml",
  "/feeds/google.xml","/feeds/google-products.xml","/feeds/google-product-feed.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml",
  "/catalog/feed.xml","/catalog/google.xml","/wp-content/uploads/google.xml","/wp-content/uploads/google-feed.xml",
  "/wp-content/uploads/woo-feed/google/xml/google.xml","/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml","/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/wppfm-feeds/google.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-json/google-product-feed/v1/xml","/wp-json/google-feed/v1/xml"
 ];
 for(const p of hist){const a=abs(root,p);if(a)cands.add(a);source.set(a,"grammar")}
 for(const p of ["/","/robots.txt","/sitemap.xml","/sitemap_index.xml","/wp-sitemap.xml","/wp-json/"]){
   const u=root+p,r=await http(u,25000);discovery.push({url:u,status:r.status,ct:r.ct,len:r.body?.length||0});
   if(r.status===200){discoverUrls(r.body,root,cands);const low=r.body.toLowerCase();if(low.includes("ctxfeed"))source.set(u,"ctxfeed-signal");if(low.includes("wppfm"))source.set(u,"wppfm-signal");}
 }
 const pd=await pluginDiscovery(root,root);
 for(const u of pd.cands){cands.add(u);source.set(u,"ctxfeed-metadata")}
 for(const p of ["/wp-json/ctxfeed/v8/","/wp-json/ctxfeed/v7/","/wp-json/ctxfeed/v1/"]){
   const r=await http(root+p,12000);if(r.status===200)discovery.push({url:root+p,status:r.status,ct:r.ct,len:r.body?.length||0});
 }
 const all=[...cands].slice(0,220);
 const checked=[];
 for(let i=0;i<all.length;i+=12){
   const batch=all.slice(i,i+12),rows=await Promise.all(batch.map(async u=>({u,v:await validate(u)})));
   for(const q of rows){checked.push({url:q.u,method:q.v.method||null,ok:q.v.ok,probe:q.v.probe||null,source:source.get(q.u)||"grammar"});if(q.v.ok)return{site:site.name,url:q.u,method:q.v.method,tested:checked.length,candidates:all.length,discovery,plugin_signals:pd.signals,browser:null,evidence:checked.slice(-20)}}
 }
 let browser=null;
 if(CF_TOKEN&&CF_ACCOUNT){
   const snap=await cf("/browser-rendering/snapshot",{url:root,formats:["content"],gotoOptions:{waitUntil:"domcontentloaded",timeout:60000},waitForTimeout:5000,viewport:{width:1440,height:900}});
   browser={snapshot:{ok:snap.ok,status:snap.status,error:snap.error||null}};
   const content=String(snap.data?.result?.content||snap.data?.content||"");
   if(content){const tmp=new Set();discoverUrls(content,root,tmp);for(const u of tmp){cands.add(u);browserDiscovered.add(u);source.set(u,"browser-rendered-html")}}
   const links=await cf("/browser-rendering/links",{url:root,visibleLinksOnly:false,gotoOptions:{waitUntil:"domcontentloaded",timeout:60000},waitForTimeout:3000,viewport:{width:1440,height:900}});
   browser.links={ok:links.ok,status:links.status,error:links.error||null};
   const ldata=links.data?.result?.links||links.data?.links||[];for(const x of Array.isArray(ldata)?ldata:[]){const a=typeof x==="string"?x:(x?.url||x?.href);if(a&&same(a,root)&&(/\.xml(?:\.gz)?(?:$|[?#])/i.test(a)||/woocommerce_gpf|woo_feed|ctxfeed|wppfm|google|merchant|shopping|product[-_]feed/i.test(a)))cands.add(a)}
   const browserCands=[...browserDiscovered].filter(u=>!checked.some(x=>x.url===u)).slice(0,20);
   for(const u of browserCands){
     const s=await cf("/browser-rendering/snapshot",{url:u,formats:["content"],gotoOptions:{waitUntil:"domcontentloaded",timeout:60000},waitForTimeout:1500,viewport:{width:1440,height:900}});
     const body=String(s.data?.result?.content||s.data?.content||"");
     const ok=s.ok&&nativeText(body);
     checked.push({url:u,method:ok?"cloudflare_snapshot":null,ok,source:"browser-explicit-candidate",snapshot_status:s.status,content_type:"rendered",len:body.length,challenge:challenge(body)});
     if(ok)return{site:site.name,url:u,method:"cloudflare_snapshot",tested:checked.length,candidates:cands.size,discovery,plugin_signals:pd.signals,browser,evidence:checked.slice(-20)}
   }
   }
 }
 return{site:site.name,url:null,method:null,tested:checked.length,candidates:cands.size,discovery,plugin_signals:pd.signals,browser,evidence:checked.slice(-30)};
}
const results=[];for(const s of sites){results.push(await probe(s));}
console.log(JSON.stringify({native_google_xml_only:true,source:"direct_http+wordpress_routes+ctxfeed+wppfm+cloudflare_browser_rendering",results},null,2));