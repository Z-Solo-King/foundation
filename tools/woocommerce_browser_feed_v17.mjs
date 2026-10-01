import {mkdir,writeFile} from "node:fs/promises";
const TARGETS=[
["PC Studio","https://www.pcstudio.in"],["Quickin Computers","https://quickincomputers.com"],["Avikaretails","https://avikaretails.com"],["IT Gadgets Online","https://itgadgetsonline.com"],
["Geekbees","https://geekbees.in"],["Ninja Dog","https://ninjadog.in"],["Network IT Store","https://networkitstore.in"],["My Nexus Infosys","https://www.mynexusinfosys.com"],["Solanki Enterprises","https://solankienterprises.com"],["AULA India","https://aulaindia.com"],
["Aarna Computers","https://aarnacomputers.com"],["Ads Store","https://adsstore.in"],["EZPZ Solutions","https://www.ezpzsolutions.in"],["GamesNComps","https://gamesncomps.com"],["hotshiftpc","https://hotshiftpc.com"],["ithunt","https://ithunt.in"],["KC Computers","https://kccomputers.co.in"],["KRG KART","https://krgkart.com"],["PC Kumar Infotech","https://pckumar.in"],["PCHubShop","https://p.chubshop.com"],
["SCL Gaming","https://sclgaming.in"],["Variety Infotech","https://varietyinfotech.com"],["Viper PC","https://viperpc.in"],["Cosmic Byte","https://www.thecosmicbyte.com"],["Meckeys","https://www.meckeys.com"],["StacksKB","https://stackskb.com"],["Theproaudio","https://www.theproaudio.com"],["Prime ABGB","https://www.primeabgb.com"],["Kryptronix Gaming","https://kryptronix.in"],["NCL Computer","https://nclcomputer.com"]];
const BLOCK=/just a moment|cf-chl-|cf-turnstile|turnstile|captcha|access denied|attention required|checking your browser|verify you are human|request blocked|sorry, you have been blocked/i;
const NS=/(?:https?:)?\/\/base\.google\.com\/ns\/1\.0/i;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function h(u){try{return new URL(u).hostname.toLowerCase().replace(/^www\./,"")}catch{return""}}
function same(a,b){return h(a)&&h(a)===h(b)}
function feedish(u){try{const x=new URL(u);return /\.xml(?:\.gz)?(?:[?#].*)?$/i.test(x.href)||/(feed|google|merchant|shopping|woo_feed|woocommerce_gpf|wppfm|webtoffee|adtribes)/i.test(x.pathname+x.search)}catch{return false}}
function valid(body){
 const s=String(body||""),t=s.trimStart();
 if(BLOCK.test(s.slice(0,50000)))return{valid:false,reason:"challenge_or_access_denied"};
 if(/^\s*<(?:urlset|sitemapindex)\b/i.test(t))return{valid:false,reason:"sitemap"};
 if(!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(t))return{valid:false,reason:"not_xml"};
 if(!NS.test(s))return{valid:false,reason:"no_google_namespace"};
 const blocks=[...[...s.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)].map(m=>m[1]),...[...s.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)].map(m=>m[1])];
 let good=0;for(const b of blocks)if(["id","title","link","price"].every(k=>new RegExp("<g:"+k+"\\b[^>]*>[\\s\\S]*?<\\/g:"+k+">","i").test(b)))good++;
 return{valid:good>0,reason:good?"validated_google_merchant_xml":"no_item_with_core_google_fields",items:blocks.length,valid_items:good};
}
async function one(name,root){
 let pw;
 try{pw=await import("playwright")}catch(e){return{site:name,root,status:"BROWSER_UNAVAILABLE",error:String(e)}}
 const chromium=pw.chromium;
 let browser;let context;const started=Date.now();
 try{
  browser=await chromium.launch({headless:true});
  context=await browser.newContext({javaScriptEnabled:true,acceptDownloads:false,serviceWorkers:"block"});
  await context.route("**/*",async route=>{
    const req=route.request(),m=(req.method()||"GET").toUpperCase();
    if(!["GET","HEAD","OPTIONS"].includes(m)){await route.abort();return}
    try{const u=new URL(req.url());if(!["http:","https:"].includes(u.protocol)||u.hostname!==new URL(root).hostname){await route.abort();return}}catch{await route.abort();return}
    await route.continue();
  });
  const page=await context.newPage(),captures=[];
  page.on("response",async resp=>{
    if(captures.length>=120)return;
    try{
      const u=resp.url(),req=resp.request(),m=(req.method()||"GET").toUpperCase();
      if(m!=="GET"||!same(u,root))return;
      const ct=(await resp.headerValue("content-type"))||"";
      if(!/(xml|json|text|javascript|html)/i.test(ct)&&!feedish(u))return;
      let b;try{b=await resp.body()}catch{return}
      if(b.length>1500000)return;
      const body=b.toString("utf8");
      captures.push({url:u,status:resp.status(),content_type:ct,bytes:b.length,body});
    }catch{}
  });
  let response;
  try{response=await page.goto(root,{waitUntil:"domcontentloaded",timeout:25000})}catch(e){}
  await page.waitForTimeout(2500);
  const html=await page.content().catch(()=> "");
  const all=captures.slice();
  if(response){
    const ct=(await response.headerValue("content-type"))||"";
    all.push({url:page.url(),status:response.status(),content_type:ct,bytes:html.length,body:html});
  }
  const candidateMap=new Map();
  const add=(u,source,rank)=>{if(feedish(u)&&same(u,root)&&(!candidateMap.has(u)||rank>candidateMap.get(u).rank))candidateMap.set(u,{url:u,source,rank})};
  for(const c of all) add(c.url,"browser_response",600);
  for(const c of all){
    const body=c.body||"";
    for(const re of [/(?:href|src|data-url|feedUrl|feed_url|product_feed)\s*=\s*["']([^"']+)["']/gi,/<loc[^>]*>\s*([^<]+?)\s*<\/loc>/gi,/https?:\/\/[^\s<>"']+/gi]){
      for(const m of body.matchAll(re)){try{const u=new URL((m[1]??m[0]).replace(/[),.;]+$/,""),root).href;add(u,"browser_page_reference",500)}catch{}}
    }
  }
  const checked=[];
  for(const c of [...candidateMap.values()].sort((a,b)=>b.rank-a.rank).slice(0,100)){
    try{
      const r=await fetch(c.url,{redirect:"follow",headers:{"user-agent":"FoundationBrowserFeedRecovery/17.0","accept":"application/xml,text/xml,*/*;q=0.1"}});
      const body=await r.text(),v=r.status===200&&same(r.url,root)?valid(body):{valid:false,reason:"http_or_redirect"};
      checked.push({url:c.url,source:c.source,rank:c.rank,status:r.status,final_url:r.url,validation:v});
      if(v.valid)return{site:name,root,status:"NATIVE_FEED_VERIFIED",winner:checked.at(-1),elapsed_s:(Date.now()-started)/1000,captures:all.map(x=>({url:x.url,status:x.status,content_type:x.content_type,bytes:x.bytes})).slice(0,120),candidate_count:candidateMap.size};
    }catch(e){checked.push({url:c.url,source:c.source,rank:c.rank,error:String(e)})}
  }
  return{site:name,root,status:BLOCK.test(html)?"BROWSER_CHALLENGE":"NO_NATIVE_FEED_VERIFIED",elapsed_s:(Date.now()-started)/1000,captures:all.map(x=>({url:x.url,status:x.status,content_type:x.content_type,bytes:x.bytes,feedish:feedish(x.url)})).slice(0,120),candidate_count:candidateMap.size,checked:checked.slice(0,100),html_head:html.slice(0,5000)}
 }catch(e){return{site:name,root,status:"BROWSER_ERROR",error:String(e)}}finally{try{await context?.close()}catch{}try{await browser?.close()}catch{}}
}
const outDir="out/woocommerce-browser-feed-v17";await mkdir(outDir,{recursive:true});const results=[];for(const t of TARGETS)results.push(await one(t[0],t[1]));const report={schema:"woocommerce-browser-feed-recovery-v17/v1",generated_at:new Date().toISOString(),target_count:30,policy:{public_read_only:true,no_cookie_injection:true,no_clearance_cookie_replay:true,no_captcha_bypass:true,no_state_changing_requests:true,merchant_xml_gate:true},results};await writeFile(outDir+"/report.json",JSON.stringify(report,null,2)+"\n");console.log(JSON.stringify({native_verified:results.filter(x=>x.status==="NATIVE_FEED_VERIFIED").length,native_urls:results.filter(x=>x.status==="NATIVE_FEED_VERIFIED").map(x=>x.winner.final_url),browser_challenge:results.filter(x=>x.status==="BROWSER_CHALLENGE").length,browser_unavailable:results.filter(x=>x.status==="BROWSER_UNAVAILABLE").length},null,2));
