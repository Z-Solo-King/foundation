import { chromium } from "playwright";
import fs from "node:fs/promises";

const TARGET = process.env.TARGET || "ALL";
const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153 Safari/537.36";
const OUT = { target: TARGET, direct: [], pages: [], network: [], scripts: [], feeds: [], products: [], errors: [] };

const rx = (s,p,flags="i") => { try { return new RegExp(p,flags).test(s||""); } catch { return false; } };
function add(a, o) { OUT[a].push(o); }
function trim(s,n=5000){ return String(s||"").slice(0,n); }
function looksProductBody(text){
  return rx(text, '(?:products|productId|sku|price|finalPrice|mrp|availability|inventory|stock|catalog|productCodes|searchResults|items|results)');
}
function looksFeed(ct, text){
  return /json|xml|rss|atom/i.test(ct||"") && looksProductBody(text);
}
async function req(url, opt={}){
  const r=await fetch(url,{redirect:"follow",headers:{"user-agent":UA,"accept":"*/*",...(opt.headers||{})},...opt});
  const text=await r.text();
  return {url:r.url,status:r.status,contentType:r.headers.get("content-type")||"",headers:Object.fromEntries(r.headers.entries()),text};
}
async function json(url,opt={}){
  const r=await req(url,{...opt,headers:{accept:"application/json,text/plain,*/*",...(opt.headers||{})}});
  let data=null; try{data=JSON.parse(r.text)}catch{}
  return {...r,data};
}
function summarize(r){
  const d=r?.data;
  const s={status:r?.status,contentType:r?.contentType,url:r?.url,bytes:r?.text?.length||0};
  if(d&&typeof d==="object"){
    s.topKeys=Object.keys(d).slice(0,30);
    const q=(name,v)=>{
      if(Array.isArray(v)) s[name+"Count"]=v.length;
      if(v&&typeof v==="object"){
        for(const k of ["total","total_count","totalCount","count","totalResults"]) if(v[k]!=null) s[name+"_"+k]=v[k];
        if(Array.isArray(v.items)) s[name+"_itemsCount"]=v.items.length;
      }
    };
    for(const k of ["products","items","results","data","catalog","searchResults","response","wizzyProducts"]) if(d[k]!=null) q(k,d[k]);
  }
  return s;
}

async function browserProbe(urls, {clickSearch=false}={}){
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({userAgent:UA,locale:"en-IN",viewport:{width:1440,height:1200}});
  const page=await context.newPage();
  const net=[];
  page.on("response", async resp=>{
    try{
      const reqq=resp.request(), u=resp.url(), ct=resp.headers()["content-type"]||"";
      const interesting = /xhr|fetch/i.test(reqq.resourceType()) || /graphql|api|json|xml|products?|search|catalog|price|stock|inventory|typesense|suggest|autocomplete/i.test(u);
      if(!interesting) return;
      const row={url:u,status:resp.status(),method:reqq.method(),resourceType:reqq.resourceType(),contentType:ct};
      if(reqq.method()!=="GET" && reqq.postData()) row.postData=trim(reqq.postData(),8000);
      if(/json|text|xml|javascript/i.test(ct) && resp.status()<500){
        try { const body=await resp.text(); row.body=trim(body,10000); row.bodyLooksProduct=looksProductBody(body); } catch {}
      }
      net.push(row);
    }catch{}
  });
  for(const u of urls){
    try{
      const p=await page.goto(u,{waitUntil:"domcontentloaded",timeout:90000});
      await page.waitForTimeout(6000);
      const html=await page.content();
      const resources=await page.evaluate(()=>performance.getEntriesByType("resource").map(x=>x.name).filter(Boolean).slice(-300));
      add("pages",{requested:u,status:p?.status()??null,finalUrl:page.url(),title:await page.title(),htmlBytes:html.length,
        markers:{next:html.includes("__NEXT_DATA__"),initialState:html.includes("INITIAL_STATE"),graphql:rx(html,"graphql"),typesense:rx(html,"typesense"),woo:rx(html,"woocommerce"),magento:rx(html,"magento"),productId:rx(html,"productId")},
        productFieldHits:[...html.matchAll(/(?:productId|sku|finalPrice|priceCurrency|mrp|availability)[^\n]{0,180}/gi)].slice(0,12).map(m=>trim(m[0],260)),
        resourceHints:resources.filter(x=>/api|graphql|json|xml|search|product|catalog|price|stock|typesense/i.test(x)).slice(0,100)
      });
      if(clickSearch){
        const inputs=await page.locator('input').evaluateAll(xs=>xs.slice(0,20).map(x=>({ph:x.placeholder,name:x.name,aria:x.getAttribute("aria-label")})));
        for(const q of ["laptop","iphone","galaxy"]){
          for(let i=0;i<inputs.length;i++){
            const loc=page.locator('input').nth(i);
            if(await loc.isVisible().catch(()=>false)){
              try { await loc.fill(q); await page.waitForTimeout(3500); } catch {}
              break;
            }
          }
          if(net.length) break;
        }
      }
    }catch(e){add("errors",{stage:"browser-page",url:u,error:String(e)})}
  }
  OUT.network.push(...net);
  await browser.close();
}

async function scriptsFor(url){
  try{
    const r=await req(url,{headers:{accept:"text/html"}});
    const scripts=[...r.text.matchAll(/<script\b[^>]+src=["']([^"']+)["']/gi)].map(m=>new URL(m[1],r.url).href);
    for(const s of [...new Set(scripts)].slice(0,30)){
      try{
        const x=await req(s,{headers:{accept:"application/javascript,text/javascript,*/*"}});
        const hits=[...x.text.matchAll(/.{0,100}(?:graphql|api(?:Url|URL)?|endpoint|typesense|productCodes|productId|finalPrice|catalog|searchservices|delivery-message|GetPrice|SearchResult|mageworx).{0,180}/gi)].slice(0,20).map(m=>trim(m[0],400));
        if(hits.length) add("scripts",{url:s,status:x.status,bytes:x.text.length,hits});
      }catch(e){add("errors",{stage:"script",url:s,error:String(e)})}
    }
  }catch(e){add("errors",{stage:"scripts-root",url,error:String(e)})}
}

async function apple(){
  const pages=["https://www.apple.com/in/","https://www.apple.com/in/shop/search?query=iphone","https://www.apple.com/in/shop/buy-iphone/iphone-17"];
  await browserProbe(pages,{clickSearch:true});
  await scriptsFor("https://www.apple.com/in/");
  const direct=[
    ["search-html","https://www.apple.com/in/shop/search?query=iphone"],
    ["search-json","https://www.apple.com/in/shop/search?query=iphone&format=json"],
    ["search-api","https://www.apple.com/in/shop/search?query=iphone&output=json"],
    ["feed-products","https://www.apple.com/in/shop/feed/products"],
    ["feed-products-xml","https://www.apple.com/in/shop/feed/products.xml"],
    ["products-json","https://www.apple.com/in/shop/products.json"],
    ["catalog-json","https://www.apple.com/in/shop/catalog.json"]
  ];
  for(const [label,u] of direct){
    try{const r=await req(u); add("direct",{label,...summarize(r),sample:trim(r.text,5000),qualifies:looksFeed(r.contentType,r.text)}); if(looksFeed(r.contentType,r.text)) add("feeds",{label,url:r.url,contentType:r.contentType,sample:trim(r.text,6000)});}catch(e){add("errors",{stage:"direct",label,error:String(e)})}
  }
}

async function acer(){
  const home="https://store.acer.com/en-in/";
  await scriptsFor(home);
  await browserProbe([home,"https://store.acer.com/en-in/catalogsearch/result/?q=laptop"]);
  const gql=`query($search:String,$pageSize:Int=50,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages}items{sku name url_key price_range{minimum_price{regular_price{value currency}final_price{value currency}}}}}}`;
  for(const u of ["https://store.acer.com/en-in/graphql","https://store.acer.com/graphql"]){
    try{const r=await json(u,{method:"POST",headers:{"content-type":"application/json","store":"default","origin":"https://store.acer.com","referer":home},body:JSON.stringify({query:gql,variables:{search:"laptop",pageSize:50,currentPage:1}})});
      add("direct",{label:"acer-graphql",url:u,...summarize(r),sample:trim(r.text,6000),qualifies:Boolean(r.data?.data?.products?.items?.length)});
    }catch(e){add("errors",{stage:"acer-graphql",url:u,error:String(e)})}
  }
}

async function asus(){
  const home="https://in.store.asus.com/";
  await scriptsFor(home); await browserProbe([home,"https://in.store.asus.com/laptops"]);
  const gql=`query($search:String,$pageSize:Int=50,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages}items{sku name url_key}}}`;
  for(const u of ["https://in.store.asus.com/graphql","https://in.store.asus.com/en-in/graphql"]){
    try{const r=await json(u,{method:"POST",headers:{"content-type":"application/json","store":"default","origin":"https://in.store.asus.com","referer":home},body:JSON.stringify({query:gql,variables:{search:"laptop",pageSize:50,currentPage:1}})}); add("direct",{label:"asus-graphql",url:u,...summarize(r),sample:trim(r.text,6000),qualifies:Boolean(r.data?.data?.products?.items?.length)});}catch(e){add("errors",{stage:"asus-graphql",url:u,error:String(e)})}
  }
  const odin=[
    ["SearchResult","https://odinapi.asus.com/recent-data/apiv2/SearchResult?SystemCode=asus&WebsiteCode=in&SearchKey=laptop&SearchType=products&SearchPDLine=&SearchPDLine2=&PDLineFilter=&TopicFilter=&CateFilter=&PageSize=50&Pages=1&LocalFlag=0&siteID=www&sitelang="],
    ["GetPrice","https://odinapi.asus.com/recent-data/apiv2/GetPrice?ProductId=UX3405MA"]
  ];
  for(const [label,u] of odin){try{const r=await json(u,{headers:{referer:"https://www.asus.com/in/"}});add("direct",{label,url:u,...summarize(r),sample:trim(r.text,6000),qualifies:looksProductBody(r.text)})}catch(e){add("errors",{stage:"odin",label,error:String(e)})}}
}

async function dell(){
  const pages=["https://www.dell.com/en-in/shop/dell-laptops-and-2-in-1-pcs/scr/laptops","https://www.dellstore.com/laptops.html"];
  await browserProbe(pages,{clickSearch:true}); await scriptsFor("https://www.dellstore.com/laptops.html");
  const hosts=["https://www.dell.com","https://www.dellstore.com"];
  const paths=[
    "/rest/V1/products?searchCriteria%5BpageSize%5D=50&searchCriteria%5BcurrentPage%5D=1",
    "/rest/V1/search?searchCriteria%5BpageSize%5D=50",
    "/rest/V1/products?searchCriteria%5BfilterGroups%5D%5B0%5D%5Bfilters%5D%5B0%5D%5Bfield%5D=visibility"
  ];
  for(const h of hosts) for(const p of paths){try{const r=await json(h+p,{headers:{referer:h+"/"}});add("direct",{label:"dell-rest",url:h+p,...summarize(r),sample:trim(r.text,5000),qualifies:r.contentType.includes("json")&&looksProductBody(r.text)})}catch(e){}}
}

async function flipkart(){
  const pages=["https://www.flipkart.com/laptops/pr?sid=6bo,b5g","https://www.flipkart.com/search?q=laptop"];
  await browserProbe(pages,{clickSearch:true});
  await scriptsFor("https://www.flipkart.com/search?q=laptop");
  const direct=[
    "https://www.flipkart.com/api/3/page/fetch",
    "https://1.rome.api.flipkart.com/api/3/page/fetch",
    "https://www.flipkart.com/api/3/search"
  ];
  for(const u of direct){try{const r=await req(u,{method:"POST",headers:{"content-type":"application/json","accept":"application/json","origin":"https://www.flipkart.com","referer":"https://www.flipkart.com/search?q=laptop"},body:JSON.stringify({query:"laptop"})});add("direct",{label:"flipkart-guessed",url:u,...summarize(r),sample:trim(r.text,5000),qualifies:r.contentType.includes("json")&&looksProductBody(r.text)})}catch(e){}}
}

async function hp(){
  const pages=["https://www.hp.com/in-en/shop","https://www.hp.com/in-en/shop/laptops"];
  await browserProbe(pages,{clickSearch:true}); await scriptsFor(pages[0]);
  const gql=`query($search:String,$pageSize:Int=50,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages}items{sku name url_key}}}`;
  for(const store of ["in-en","default","IN","en_IN"]){try{const r=await json("https://www.hp.com/in-en/shop/graphql",{method:"POST",headers:{"content-type":"application/json","accept":"application/json","store":store,"origin":"https://www.hp.com","referer":"https://www.hp.com/in-en/shop"},body:JSON.stringify({query:gql,variables:{search:"laptop",pageSize:50,currentPage:1}})});add("direct",{label:"hp-graphql-"+store,...summarize(r),sample:trim(r.text,6000),qualifies:Boolean(r.data?.data?.products?.items?.length)})}catch(e){}}
}

async function samsung(){
  const pages=["https://www.samsung.com/in/","https://www.samsung.com/in/search/?searchvalue=galaxy","https://www.samsung.com/in/smartphones/"];
  await browserProbe(pages,{clickSearch:true}); await scriptsFor(pages[1]);
  const candidates=[
    "https://www.samsung.com/in/api/v1/products/search?query=a:relevance&pageSize=100",
    "https://www.samsung.com/in/api/v1/products/search?query=galaxy&pageSize=100",
    "https://www.samsung.com/in/products/search?query=a:relevance&pageSize=100",
    "https://www.samsung.com/in/api/v2/products/search?query=galaxy&pageSize=100"
  ];
  for(const u of candidates){try{const r=await json(u,{headers:{referer:"https://www.samsung.com/in/search/?searchvalue=galaxy"}});add("direct",{label:"samsung-search",url:r.url,...summarize(r),sample:trim(r.text,6000),qualifies:r.contentType.includes("json")&&looksProductBody(r.text)});const codes=[...r.text.matchAll(/(?:productCode|code)["']?\s*[:=]\s*["']?([A-Za-z0-9_-]{4,40})/gi)].map(m=>m[1]).slice(0,20);if(codes.length){for(const base of ["https://www.samsung.com/in/api/v1/products","https://www.samsung.com/in/products"]){try{const b=await json(base+"?productCodes="+encodeURIComponent(codes.slice(0,10).join(","))+"&fields=FULL",{headers:{referer:"https://www.samsung.com/in/"}});add("direct",{label:"samsung-bulk",url:b.url,...summarize(b),sample:trim(b.text,6000),qualifies:b.contentType.includes("json")&&looksProductBody(b.text)})}catch(e){}}}}catch(e){}}
}

async function vijay(){
  const cat="https://www.vijaysales.com/c/laptops";
  const browser=await chromium.launch({headless:true}); const context=await browser.newContext({userAgent:UA,locale:"en-IN",viewport:{width:1440,height:1200}}); const page=await context.newPage(); const net=[];
  page.on("response",async resp=>{try{const q=resp.request();const u=resp.url();if(/xhr|fetch/i.test(q.resourceType())||/api|json|product|search|price|stock/i.test(u)){const row={url:u,status:resp.status(),method:q.method(),resourceType:q.resourceType(),contentType:resp.headers()["content-type"]||""};if(q.postData())row.postData=trim(q.postData(),6000);if(/json|text/i.test(row.contentType)&&resp.status()<500)try{row.body=trim(await resp.text(),9000)}catch{};net.push(row)}}catch{}}); 
  try{await page.goto(cat,{waitUntil:"domcontentloaded",timeout:90000});await page.waitForTimeout(7000);const html=await page.content();
    const hrefs=[...html.matchAll(/href=["']([^"']*\/p\/[0-9]+[^"']*)["']/gi)].map(m=>new URL(m[1],page.url()).href);
    add("pages",{requested:cat,status:200,htmlBytes:html.length,productHrefs:[...new Set(hrefs)].slice(0,30)});
    for(const u of [...new Set(hrefs)].slice(0,3)){try{const r=await page.goto(u,{waitUntil:"domcontentloaded",timeout:60000});await page.waitForTimeout(4000);const body=await page.content();add("pages",{requested:u,status:r?.status()??null,finalUrl:page.url(),htmlBytes:body.length,productFieldHits:[...body.matchAll(/(?:sku|productId|price|finalPrice|mrp|availability|stock)[^\n]{0,180}/gi)].slice(0,15).map(m=>trim(m[0],300))})}catch{}} 
  }catch(e){add("errors",{stage:"vijay",error:String(e)})}
  OUT.network.push(...net); await browser.close();
  await scriptsFor(cat);
}

async function run(){
  const fn={Apple:apple,Acer:acer,ASUS:asus,Dell:dell,Flipkart:flipkart,HP:hp,Samsung:samsung,"Vijay Sales":vijay}[TARGET];
  if(fn) await fn(); else {for(const f of Object.values({Apple:apple,Acer:acer,ASUS:asus,Dell:dell,Flipkart:flipkart,HP:hp,Samsung:samsung,"Vijay Sales":vijay})) await f();}
  for(const p of OUT.network) if(p.bodyLooksProduct||looksFeed(p.contentType,p.body)) add("products",{url:p.url,status:p.status,method:p.method,contentType:p.contentType,sample:trim(p.body,7000)});
  await fs.writeFile("deep-probe-result.json",JSON.stringify(OUT,null,2));
  const qualifying=[...OUT.direct.filter(x=>x.qualifies),...OUT.network.filter(x=>x.bodyLooksProduct&&(/json|xml/i.test(x.contentType||"")))];
  console.log(JSON.stringify({target:TARGET,direct:OUT.direct.length,network:OUT.network.length,scripts:OUT.scripts.length,qualifying:qualifying.slice(0,20).map(x=>({url:x.url,status:x.status,contentType:x.contentType,qualifies:x.qualifies||x.bodyLooksProduct,label:x.label}))},null,2));
}
run().catch(async e=>{OUT.errors.push({stage:"fatal",error:String(e)});await fs.writeFile("deep-probe-result.json",JSON.stringify(OUT,null,2));process.exitCode=1});
