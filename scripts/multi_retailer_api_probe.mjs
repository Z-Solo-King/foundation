import { chromium } from "playwright";
import fs from "node:fs/promises";

const TARGET = process.env.TARGET;
const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";
const OUT = { target: TARGET, probes: [], network: [], errors: [] };

function add(label, data) { OUT.probes.push({ label, ...data }); }
function interesting(u) {
  return /graphql|products?|search|catalog|price|stock|inventory|rest|api|openapi|servicesv2|typesense/i.test(u);
}
async function http(url, options={}) {
  const res = await fetch(url, {
    redirect: "follow",
    ...options,
    headers: { "user-agent": UA, "accept": "*/*", ...(options.headers || {}) }
  });
  const text = await res.text();
  return { status:res.status, contentType:res.headers.get("content-type") || "", url:res.url, text };
}
async function json(url, options={}) {
  const r = await http(url, { headers:{accept:"application/json",...(options.headers||{})}, ...options });
  let data=null, parseError=null;
  try { data=JSON.parse(r.text); } catch(e){ parseError=String(e); }
  return {...r,data,parseError};
}
function summarize(data) {
  if (!data || typeof data !== "object") return {};
  const d=data.data ?? data;
  const out={topKeys:Object.keys(data).slice(0,25)};
  const walk=(name,v)=>{
    if(Array.isArray(v)){out[name+"_count"]=v.length}
    else if(v&&typeof v==="object"){
      if(Array.isArray(v.items)) out[name+"_items_count"]=v.items.length;
      for(const k of ["total_count","totalCount","total","count","totalResults"]) if(v[k]!=null) out[name+"_"+k]=v[k];
      for(const k of ["pagination","page","page_info","pageInfo","meta"]) if(v[k]!=null) out[name+"_"+k]=v[k];
    }
  };
  for(const k of ["products","items","results","searchResults","wizzyProducts","response","catalog"]) if(d?.[k]!=null) walk(k,d[k]);
  return out;
}
async function browse(urls, wait=5000) {
  const browser=await chromium.launch({headless:true});
  const context=await browser.newContext({userAgent:UA,locale:"en-IN",viewport:{width:1440,height:1200}});
  const page=await context.newPage();
  const seen=new Map();
  page.on("response",resp=>{
    try{
      const req=resp.request();
      if(interesting(resp.url()) || ["xhr","fetch"].includes(req.resourceType())){
        const row={url:resp.url(),status:resp.status(),contentType:resp.headers()["content-type"]||"",resourceType:req.resourceType(),method:req.method()};
        if(req.method()!=="GET" && req.postData()) row.postData=req.postData().slice(0,7000);
        if(!seen.has(resp.url()) || req.method()!=="GET") seen.set(resp.url(),row);
      }
    }catch{}
  });
  for(const u of urls){
    try{
      const resp=await page.goto(u,{waitUntil:"domcontentloaded",timeout:90000});
      await page.waitForTimeout(wait);
      add("page",{requested:u,status:resp?.status()??null,finalUrl:page.url(),title:await page.title()});
    }catch(e){OUT.errors.push({stage:"page",url:u,error:String(e)})}
  }
  OUT.network.push(...seen.values());
  await browser.close();
}
async function acer(){
  const home=await http("https://store.acer.com/en-in/");
  add("home",{status:home.status,contentType:home.contentType,bytes:home.text.length});
  const q=`query($search:String,$pageSize:Int=20,$currentPage:Int=1){
    products(search:$search,pageSize:$pageSize,currentPage:$currentPage){
      total_count page_info{current_page page_size total_pages}
      items{sku name url_key}
    }
  }`;
  const r=await json("https://store.acer.com/en-in/graphql",{method:"POST",headers:{
    "content-type":"application/json","accept":"application/json","store":"default",
    "origin":"https://store.acer.com","referer":"https://store.acer.com/en-in/"
  },body:JSON.stringify({query:q,variables:{search:"laptop",pageSize:50,currentPage:1}})});
  add("native-graphql",{url:r.url,status:r.status,contentType:r.contentType,summary:summarize(r.data),sample:r.text.slice(0,3500),parseError:r.parseError});
  await browse(["https://store.acer.com/en-in/"],4000);
}
async function apple(){
  const sm=await http("https://www.apple.com/in/shop/sitemaps/product.xml");
  const urls=[...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
  add("sitemap",{status:sm.status,contentType:sm.contentType,bytes:sm.text.length,urlCount:urls.length,firstUrls:urls.slice(0,8)});
  const sample=urls.find(u=>/iphone|macbook|ipad|watch|airpods/i.test(u))||urls[0];
  if(!sample)return;
  const p=await http(sample,{headers:{accept:"text/html"}});
  const skus=[...p.text.matchAll(/(?:sku|partNumber|productNumber)["':\s]+["']?([A-Za-z0-9.\/-]{4,20})/gi)].map(m=>m[1]);
  const parts=[...p.text.matchAll(/parts\.0=([A-Za-z0-9._\/-]+)/g)].map(m=>m[1]);
  const ids=[...new Set([...parts,...skus])].slice(0,4);
  add("pdp",{url:sample,status:p.status,bytes:p.text.length,ids,priceHits:[...p.text.matchAll(/(?:fullPrice|priceCurrency|price>)[^\n]{0,180}/gi)].slice(0,5).map(m=>m[0].slice(0,260))});
  for(const id of ids.slice(0,3)){
    const d=await http("https://www.apple.com/shop/delivery-message?parts.0="+encodeURIComponent(id),{headers:{accept:"application/json,text/plain,*/*",referer:sample}});
    add("delivery-message",{id,status:d.status,contentType:d.contentType,sample:d.text.slice(0,1800)});
  }
}
async function asus(){
  const direct=await http("https://in.store.asus.com/graphql",{headers:{accept:"application/json",store:"default",referer:"https://in.store.asus.com/"}}).catch(e=>({status:0,text:"",error:String(e)}));
  add("store-graphql-get",{status:direct.status,contentType:direct.contentType||"",sample:direct.text?.slice(0,1200),error:direct.error});
  const sr=await json("https://odinapi.asus.com/recent-data/apiv2/SearchResult?SystemCode=asus&WebsiteCode=in&SearchKey=laptop&SearchType=products&SearchPDLine=&SearchPDLine2=&PDLineFilter=&TopicFilter=&CateFilter=&PageSize=20&Pages=1&LocalFlag=0&siteID=www&sitelang=",{headers:{accept:"application/json",referer:"https://www.asus.com/in/"}});
  add("odin-search",{url:sr.url,status:sr.status,contentType:sr.contentType,summary:summarize(sr.data),sample:sr.text.slice(0,5000),parseError:sr.parseError});
  const ids=[...sr.text.matchAll(/(?:ProductId|productId|ProductID|id|model)[^A-Za-z0-9]{0,8}([A-Za-z0-9._-]{4,40})/gi)].map(m=>m[1]).filter(x=>/[A-Za-z]/.test(x)).slice(0,8);
  add("odin-search-ids",{ids});
  if(ids.length){
    const pr=await json("https://odinapi.asus.com/recent-data/apiv2/GetPrice?ProductId="+encodeURIComponent(ids.slice(0,6).join(",")),{headers:{accept:"application/json",referer:"https://www.asus.com/in/"}});
    add("odin-price",{url:pr.url,status:pr.status,contentType:pr.contentType,summary:summarize(pr.data),sample:pr.text.slice(0,5000),parseError:pr.parseError});
  }
  await browse(["https://in.store.asus.com/"],5000);
}
async function croma(){
  for(const query of [":relevance","laptops:relevance"]){
    const u="https://api.croma.com/searchservices/v1/search?currentPage=0&query="+encodeURIComponent(query)+"&fields=FULL&channel=WEB";
    const r=await json(u,{headers:{origin:"https://www.croma.com",referer:"https://www.croma.com/"}});
    add("search-api",{query,url:r.url,status:r.status,contentType:r.contentType,summary:summarize(r.data),sample:r.text.slice(0,3500),parseError:r.parseError});
  }
}
async function dell(){
  await browse(["https://www.dell.com/en-in/shop/dell-laptops-and-2-in-1-pcs/scr/laptops","https://www.dellstore.com/laptops.html"],5000);
  for(const host of ["https://www.dell.com","https://www.dellstore.com"]){
    const u=host+"/rest/V1/products?searchCriteria%5BpageSize%5D=50&searchCriteria%5BcurrentPage%5D=1";
    const r=await json(u,{headers:{accept:"application/json",referer:host+"/"}});
    add("rest-products",{url:r.url,status:r.status,contentType:r.contentType,summary:summarize(r.data),sample:r.text.slice(0,2200),parseError:r.parseError});
  }
  add("interesting-network",{requests:OUT.network.filter(x=>/dellstore\.com|dell\.com/i.test(x.url)&&/typesense|search|api|product|price|stock|rest/i.test(x.url)).slice(0,30)});
}
async function flipkart(){
  const u="https://www.flipkart.com/laptops/pr?sid=6bo,b5g";
  const raw=await http(u,{headers:{accept:"text/html"}});
  add("raw-html",{status:raw.status,bytes:raw.text.length,initialStateMarker:raw.text.includes("__INITIAL_STATE__"),initialStateEmpty:/window\.__INITIAL_STATE__\s*=\s*\{\s*\}/.test(raw.text),productIdHits:[...raw.text.matchAll(/productId[^\d]{0,40}(\d{5,})/gi)].slice(0,10).map(m=>m[1]),finalPriceHits:[...raw.text.matchAll(/finalPrice[^\d]{0,40}(\d{3,})/gi)].slice(0,10).map(m=>m[1])});
  await browse([u],5000);
}
async function hp(){
  const q=`query($search:String,$pageSize:Int=20,$currentPage:Int=1){
    products(search:$search,pageSize:$pageSize,currentPage:$currentPage){
      total_count page_info{current_page page_size total_pages}
      items{sku name url_key}
    }
  }`;
  for(const store of ["in-en","default"]){
    const r=await json("https://www.hp.com/in-en/shop/graphql",{method:"POST",headers:{
      "content-type":"application/json","accept":"application/json","store":store,
      "origin":"https://www.hp.com","referer":"https://www.hp.com/in-en/shop"
    },body:JSON.stringify({query:q,variables:{search:"laptop",pageSize:50,currentPage:1}})});
    add("graphql-native-replay",{store,url:r.url,status:r.status,contentType:r.contentType,summary:summarize(r.data),sample:r.text.slice(0,3000),parseError:r.parseError});
  }
  await browse(["https://www.hp.com/in-en/shop","https://www.hp.com/in-en/shop/laptops"],5000);
}
async function lenovo(){
  const sm=await http("https://www.lenovo.com/sitemap-auto/037-intsitemap-in-en.xml");
  const urls=[...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]);
  const sample=urls.find(u=>/\/p\//i.test(u));
  add("sitemap",{status:sm.status,bytes:sm.text.length,urlCount:urls.length,sample});
  if(sample){
    const p=await http(sample,{headers:{accept:"text/html",referer:"https://www.lenovo.com/"}}); 
    const code=(sample.match(/\/([A-Za-z0-9_-]{8,30})\/?$/)||[])[1]||"";
    await browse([sample],5000);
    const price=OUT.network.find(x=>/openapi\.lenovo\.com\/in\/en\/detail\/price\/batch\/get/i.test(x.url));
    const priceUrl=price?.url||("https://openapi.lenovo.com/in/en/detail/price/batch/get?preSelect=1&mcode="+encodeURIComponent(code)+"&configId=&enteredCode=");
    const pr=await json(priceUrl,{headers:{accept:"application/json",referer:sample}});
    add("price-api",{url:priceUrl,status:pr.status,contentType:pr.contentType,summary:summarize(pr.data),sample:pr.text.slice(0,5000),parseError:pr.parseError});
  }
}
async function reliance(){
  for(const u of [
    "https://www.reliancedigital.in/ext/raven-api/catalog/v1.0/products?page_no=1&page_size=50",
    "https://www.reliancedigital.in/ext/raven-api/catalog/v1.0/products?q=laptop&page_no=1&page_size=50"
  ]){
    const r=await json(u,{headers:{accept:"application/json",referer:"https://www.reliancedigital.in/"}});
    add("catalog-api",{url:r.url,status:r.status,contentType:r.contentType,summary:summarize(r.data),sample:r.text.slice(0,3000),parseError:r.parseError});
  }
}
async function samsung(){
  const pages=[
    "https://www.samsung.com/in/",
    "https://www.samsung.com/in/smartphones/",
    "https://www.samsung.com/in/search/?searchvalue=galaxy"
  ];
  await browse(pages,6000);
  const raw=await http("https://www.samsung.com/in/search/?searchvalue=galaxy",{headers:{accept:"text/html"}});
  const clues=[...new Set([
    ...[...raw.text.matchAll(/https?:\/\/[^"'\\s<>]+/gi)].map(m=>m[0]),
    ...[...raw.text.matchAll(/(?:\/|https?:)[^"'\\s<>]*(?:products\/search|\/products\?productCodes=|searchapi)[^"'\\s<>]*/gi)].map(m=>m[0])
  ])].filter(x=>/products|searchapi|productCodes/i.test(x)).slice(0,50);
  add("source-clues",{status:raw.status,bytes:raw.text.length,clues});
  add("product-network",{requests:OUT.network.filter(x=>/products\\/search|\\/products\\?productCodes=|searchapi/i.test(x.url)).slice(0,30)});
}
async function vijay(){
  const url="https://www.vijaysales.com/c/laptops";
  const p=await http(url,{headers:{accept:"text/html"}});
  const hrefs=[...p.text.matchAll(/href=["']([^"']*\/p\/[0-9]+[^"']*)["']/gi)].map(m=>m[1]);
  add("category",{status:p.status,bytes:p.text.length,pdpHrefs:hrefs.slice(0,12),ids:[...new Set(hrefs.map(h=>(h.match(/\/p\/(\d+)/)||[])[1]).filter(Boolean))].slice(0,20)});
  await browse([url],5000);
  const networks=OUT.network.filter(x=>/vijaysales\.com/i.test(x.url)&&/api|search|product|catalog|ajax|graphql/i.test(x.url)).slice(0,50);
  add("product-network",{requests:networks});
  if(hrefs[0]){
    const full=new URL(hrefs[0],url).toString();
    const pdp=await http(full,{headers:{accept:"text/html",referer:url}});
    add("pdp",{url:full,status:pdp.status,finalUrl:pdp.url,bytes:pdp.text.length,priceHits:[...pdp.text.matchAll(/(?:₹|Rs\\.?)[^<]{0,100}/gi)].slice(0,8).map(m=>m[0].slice(0,180))});
  }
}
const FNS={Acer:acer,Apple:apple,ASUS:asus,Croma:croma,Dell:dell,Flipkart:flipkart,HP:hp,Lenovo:lenovo,"Reliance Digital":reliance,Samsung:samsung,"Vijay Sales":vijay};
if(!FNS[TARGET]) throw new Error("Unknown target "+TARGET);
try{await FNS[TARGET]();}catch(e){OUT.errors.push({stage:"top-level",error:String(e)})}
OUT.network=OUT.network.filter(x=>/xhr|fetch/i.test(x.resourceType)||interesting(x.url));
await fs.writeFile("probe-result.json",JSON.stringify(OUT,null,2));
console.log(JSON.stringify(OUT,null,2));
