import { chromium } from "playwright";
import fs from "node:fs/promises";
import { URL } from "node:url";

const target = process.env.TARGET;
const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";
const results = { target, probes: [], network: [], errors: [] };

function add(label, data) { results.probes.push({ label, ...data }); }
function isInteresting(url) {
  return /(?:graphql|api|rest\/|products?|search|catalog|price|stock|sitemap|delivery)/i.test(url);
}
async function fetchText(url, options={}) {
  const r = await fetch(url, {
    redirect: "follow",
    ...options,
    headers: { "user-agent": UA, "accept": "*/*", ...(options.headers || {}) }
  });
  const text = await r.text();
  return { status:r.status, contentType:r.headers.get("content-type") || "", url:r.url, text };
}
async function fetchJson(url, options={}) {
  const r = await fetchText(url, { headers: { accept:"application/json", ...(options.headers||{}) }, ...options });
  let json = null, parseError = null;
  try { json = JSON.parse(r.text); } catch (e) { parseError = String(e); }
  return { ...r, json, parseError };
}
function bodySummary(json) {
  if (!json || typeof json !== "object") return {};
  const data = json.data ?? json;
  const out = { topKeys:Object.keys(json).slice(0,30) };
  for (const key of ["products","items","results","data","searchResults","wizzyProducts"]) {
    const v = data?.[key];
    if (Array.isArray(v)) out[key + "_count"] = v.length;
    else if (v && typeof v === "object") {
      if (Array.isArray(v.items)) out[key+"_items_count"] = v.items.length;
      for (const n of ["total_count","totalCount","total","totalResults"]) if (v[n] != null) out[key+"_"+n] = v[n];
      if (v.page_info) out[key+"_page_info"] = v.page_info;
      if (v.pageInfo) out[key+"_pageInfo"] = v.pageInfo;
    }
  }
  return out;
}
async function browserProbe(startUrls, opts={}) {
  const browser = await chromium.launch({headless:true});
  const context = await browser.newContext({ userAgent:UA, locale:"en-IN", viewport:{width:1440,height:1200} });
  const page = await context.newPage();
  const seen = new Map();
  page.on("response", async (resp) => {
    try {
      const req = resp.request();
      if (isInteresting(resp.url()) || ["xhr","fetch"].includes(req.resourceType())) {
        const row = { url:resp.url(), status:resp.status(), contentType:resp.headers()["content-type"]||"", resourceType:req.resourceType(), method:req.method() };
        if (req.method() !== "GET" && req.postData()) row.postData = req.postData()?.slice(0,6000);
        const prev = seen.get(resp.url());
        if (!prev || prev.status !== 200 || row.method !== "GET") seen.set(resp.url(), row);
      }
    } catch {}
  });
  for (const u of startUrls) {
    try {
      const resp = await page.goto(u, {waitUntil:"domcontentloaded", timeout:opts.timeout || 90000});
      await page.waitForTimeout(opts.wait || 4000);
      add("page", { requested:u, status:resp?.status()??null, finalUrl:page.url(), title:await page.title() });
    } catch (e) {
      results.errors.push({ stage:"page", url:u, error:String(e) });
    }
  }
  results.network.push(...seen.values());
  await browser.close();
}

async function probeAcer() {
  await browserProbe(["https://store.acer.com/en-in/"], {wait:5000});
  const graphql = results.network.find(x => x.url.includes("/graphql") && x.method === "POST");
  add("graphql-capture", graphql ? {found:true,url:graphql.url,postData:graphql.postData,storeHeader:"default"} : {found:false});
  const direct = [
    "https://store.acer.com/en-in/graphql",
  ];
  const nativeQuery = `query($search:String,$pageSize:Int=20,$currentPage:Int=1){
    products(search:$search,pageSize:$pageSize,currentPage:$currentPage){
      total_count page_info{current_page page_size total_pages}
      items{sku name url_key}
    }
  }`;
  for (const ep of direct) {
    try {
      const home = await fetchText("https://store.acer.com/en-in/", {headers:{accept:"text/html"}});
      const cookies = home.headers;
      const resp = await fetchJson(ep,{
        method:"POST",
        headers:{
          "content-type":"application/json","accept":"application/json","store":"default",
          "origin":"https://store.acer.com","referer":"https://store.acer.com/en-in/"
        },
        body:JSON.stringify({query:nativeQuery,variables:{search:"laptop",pageSize:50,currentPage:1}})
      });
      add("native-graphql-replay",{url:ep,status:resp.status,contentType:resp.contentType,summary:bodySummary(resp.json),sample:resp.text.slice(0,3500),parseError:resp.parseError});
    } catch(e){ results.errors.push({stage:"acer-native-graphql",error:String(e)}); }
  }
  if (graphql?.postData) {
    try {
      const payload = JSON.parse(graphql.postData);
      payload.variables = payload.variables || {};
      if ("pageSize" in payload.variables) payload.variables.pageSize = 50;
      const r = await fetchJson(graphql.url, {
        method:"POST",
        headers:{
          "content-type":"application/json",
          "accept":"application/json",
          "store":"default",
          "origin":"https://store.acer.com",
          "referer":"https://store.acer.com/en-in/"
        },
        body:JSON.stringify(payload)
      });
      add("graphql-replay", {status:r.status,contentType:r.contentType,summary:bodySummary(r.json),parseError:r.parseError});
    } catch(e) { results.errors.push({stage:"graphql-replay",error:String(e)}); }
  }
}

async function probeApple() {
  const sm = await fetchText("https://www.apple.com/in/shop/sitemaps/product.xml");
  add("sitemap", {status:sm.status,contentType:sm.contentType,bytes:sm.text.length,firstUrls:[...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].slice(0,8).map(m=>m[1])});
  const urls = [...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]).filter(Boolean);
  const sample = urls.find(u=>/iphone|macbook|ipad|watch|airpods/i.test(u)) || urls[0];
  if (sample) {
    const p = await fetchText(sample,{headers:{accept:"text/html"}});
    const priceHits = [...p.text.matchAll(/(?:fullPrice|price|amount)[^\n]{0,180}/gi)].slice(0,10).map(m=>m[0].slice(0,220));
    add("pdp", {url:sample,status:p.status,bytes:p.text.length,priceRegexHits:priceHits});
    const ids = [...p.text.matchAll(/parts\.0=([A-Za-z0-9._-]+)/g)].map(m=>m[1]).slice(0,5);
    for (const id of ids.slice(0,2)) {
      const d=await fetchText("https://www.apple.com/shop/delivery-message?parts.0="+encodeURIComponent(id),{headers:{accept:"application/json,text/plain,*/*",referer:sample}});
      add("delivery-message", {id,status:d.status,contentType:d.contentType,sample:d.text.slice(0,1200)});
    }
  }
}

async function probeAsus() {
  await browserProbe(["https://in.store.asus.com/"], {wait:7000});
  const gql = results.network.find(x=>/in\.store\.asus\.com\/graphql/i.test(x.url) && x.method==="POST");
  add("graphql-capture",gql?{found:true,url:gql.url,postData:gql.postData}:{found:false});
  const price = results.network.find(x=>/odinapi\.asus\.com/i.test(x.url) && /getprice/i.test(x.url));
  add("odinapi-price-capture",price?{found:true,url:price.url,postData:price.postData}:{found:false});
}

async function probeCroma() {
  const url="https://api.croma.com/searchservices/v1/search?currentPage=0&query=:relevance&fields=FULL&channel=WEB";
  const r=await fetchJson(url,{headers:{accept:"application/json",origin:"https://www.croma.com",referer:"https://www.croma.com/"}});
  add("search-api",{url,status:r.status,contentType:r.contentType,summary:bodySummary(r.json),parseError:r.parseError,sample:r.text.slice(0,2500)});
}

async function probeDell() {
  for (const url of [
    "https://www.dell.com/en-in/shop/dell-laptops-and-2-in-1-pcs/scr/laptops",
    "https://www.dell.com/rest/V1/products?searchCriteria%5BpageSize%5D=50&searchCriteria%5BcurrentPage%5D=1"
  ]) {
    if (url.includes("/rest/")) {
      const r=await fetchJson(url,{headers:{accept:"application/json",referer:"https://www.dell.com/en-in/"}});
      add("rest-products",{url,status:r.status,contentType:r.contentType,summary:bodySummary(r.json),sample:r.text.slice(0,2500),parseError:r.parseError});
    } else await browserProbe([url],{wait:5000});
  }
  const product = results.network.find(x=>/\/rest\/V1\/products/i.test(x.url));
  add("rest-capture",product?{found:true,url:product.url,method:product.method,postData:product.postData}:{found:false});
  const stock = results.network.find(x=>/\/rest\/V1\/stockStatuses\//i.test(x.url));
  add("stock-capture",stock?{found:true,url:stock.url}:{found:false});
}

async function probeFlipkart() {
  const raw=await fetchText("https://www.flipkart.com/laptops/pr?sid=6bo,b5g",{headers:{accept:"text/html"}});
  add("raw-html",{status:raw.status,bytes:raw.text.length,initialStateMarker:raw.text.includes("__INITIAL_STATE__"),productIdHits:[...raw.text.matchAll(/productId[^\\d]{0,40}(\\d{5,})/gi)].slice(0,10).map(m=>m[1]),finalPriceHits:[...raw.text.matchAll(/finalPrice[^\\d]{0,40}(\\d{3,})/gi)].slice(0,10).map(m=>m[1])});
  await browserProbe(["https://www.flipkart.com/laptops/pr?sid=6bo,b5g"],{wait:5000});
  // Re-run DOM inspection separately so the state blob is not lost in network capture.
  const browser=await chromium.launch({headless:true});
  const page=await browser.newPage({userAgent:UA,locale:"en-IN"});
  try {
    await page.goto("https://www.flipkart.com/laptops/pr?sid=6bo,b5g",{waitUntil:"domcontentloaded",timeout:90000});
    await page.waitForTimeout(3500);
    const state=await page.evaluate(() => {
      const w=window;
      const keys=Object.keys(w).filter(k=>/INITIAL_STATE/i.test(k));
      const candidates=keys.map(k=>({key:k,type:typeof w[k],len:JSON.stringify(w[k]||"").length})).slice(0,20);
      return candidates;
    });
    add("initial-state-keys",{state});
    const text=await page.content();
    add("html-state-regex",{found:/INITIAL_STATE/.test(text),productIdHits:[...text.matchAll(/productId[^\d]{0,30}(\d{6,})/gi)].slice(0,10).map(m=>m[1]),finalPriceHits:[...text.matchAll(/finalPrice[^\d]{0,40}(\d{3,})/gi)].slice(0,10).map(m=>m[1])});
  }catch(e){results.errors.push({stage:"flipkart-state",error:String(e)})}
  await browser.close();
}

async function probeHP() {
  await browserProbe(["https://www.hp.com/in-en/shop"],{wait:7000});
  const gqls=results.network.filter(x=>/hp\.com\/in-en\/shop\/graphql/i.test(x.url));
  add("graphql-capture",{count:gqls.length,requests:gqls.slice(0,5)});
}

async function probeLenovo() {
  const sm=await fetchText("https://www.lenovo.com/sitemap-auto/037-intsitemap-in-en.xml");
  add("sitemap",{status:sm.status,contentType:sm.contentType,bytes:sm.text.length,firstUrls:[...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].slice(0,10).map(m=>m[1])});
  const urls=[...sm.text.matchAll(/<loc>([^<]+)<\/loc>/g)].map(m=>m[1]).filter(u=>/lenovo\.com\/in\/en\/p\//i.test(u));
  const sample=urls[0];
  if(sample){
    const p=await fetchText(sample,{headers:{accept:"text/html",referer:"https://www.lenovo.com/"}});
    const codes=[...p.text.matchAll(/(?:mcode|productCode|product_code|sku)[^A-Za-z0-9]{0,8}([A-Za-z0-9._-]{3,40})/gi)].map(m=>m[1]).filter(x=>x.length>3).slice(0,12);
    add("pdp",{url:sample,status:p.status,bytes:p.text.length,codes});
    await browserProbe([sample],{wait:5000});
  }
  const lenovoApi=results.network.find(x=>/openapi\.lenovo\.com/i.test(x.url) && /price|batch/i.test(x.url));
  add("price-api-capture",lenovoApi?{found:true,url:lenovoApi.url,method:lenovoApi.method,postData:lenovoApi.postData}:{found:false});
}

async function probeReliance() {
  const url="https://www.reliancedigital.in/ext/raven-api/catalog/v1.0/products?page_no=1&page_size=50";
  const r=await fetchJson(url,{headers:{accept:"application/json",referer:"https://www.reliancedigital.in/"}});
  add("catalog-api",{url,status:r.status,contentType:r.contentType,summary:bodySummary(r.json),sample:r.text.slice(0,4000),parseError:r.parseError});
}

async function probeSamsung() {
  await browserProbe(["https://www.samsung.com/in/"],{wait:7000});
  const api=results.network.filter(x=>/products\/search|\/products\?productCodes=/i.test(x.url));
  add("product-api-capture",{count:api.length,requests:api.slice(0,12)});
  // A direct generic search request is attempted only against an observed Samsung host.
  const observed=api.find(x=>/products\/search/i.test(x.url));
  if(observed){
    const u=new URL(observed.url);
    u.searchParams.set("query","a:relevance");
    u.searchParams.set("pageSize","100");
    const r=await fetchJson(u.toString(),{headers:{accept:"application/json",referer:"https://www.samsung.com/in/"}});
    add("search-replay",{url:u.toString(),status:r.status,contentType:r.contentType,summary:bodySummary(r.json),sample:r.text.slice(0,3000),parseError:r.parseError});
  }
}

async function probeVijaySales() {
  const url="https://www.vijaysales.com/c/laptops";
  const p=await fetchText(url,{headers:{accept:"text/html"}});
  const ids=[...p.text.matchAll(/\/p\/(\d+)/g)].map(m=>m[1]);
  add("category",{url,status:p.status,contentType:p.contentType,bytes:p.text.length,pdpIds:[...new Set(ids)].slice(0,20)});
  const id=[...new Set(ids)][0];
  if(id){
    const pdp=await fetchText("https://www.vijaysales.com/p/"+id,{headers:{accept:"text/html",referer:url}});
    add("pdp",{id,status:pdp.status,bytes:pdp.text.length,priceHits:[...pdp.text.matchAll(/(?:₹|Rs\.?)[^<]{0,80}/gi)].slice(0,15).map(m=>m[0].slice(0,180))});
  }
}

const fn = {
  Acer:probeAcer, Apple:probeApple, ASUS:probeAsus, Croma:probeCroma, Dell:probeDell,
  Flipkart:probeFlipkart, HP:probeHP, Lenovo:probeLenovo, "Reliance Digital":probeReliance,
  Samsung:probeSamsung, "Vijay Sales":probeVijaySales
}[target];

if (!fn) throw new Error("Unknown TARGET="+target);
try { await fn(); } catch (e) { results.errors.push({stage:"top-level",error:String(e)}); }
await fs.writeFile("probe-result.json", JSON.stringify(results,null,2));
console.log(JSON.stringify(results,null,2));
