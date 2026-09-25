import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const TARGET = process.env.TARGET || "";
const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";
const OUT = { target: TARGET, direct: [], browser: [], errors: [], qualification: [] };

function trim(v, n = 9000) { return String(v ?? "").slice(0, n); }
function productish(v) {
  const s = String(v ?? "").toLowerCase();
  const hits = ["product", "products", "sku", "price", "finalprice", "sellingprice", "mrp", "listingid", "productid", "iteminfo"];
  return hits.filter(x => s.includes(x)).length >= 2;
}
async function http(url, options = {}) {
  const response = await fetch(url, { redirect: "follow", headers: { "user-agent": UA, "accept": "*/*", ...(options.headers || {}) }, ...options });
  return { url: response.url, status: response.status, contentType: response.headers.get("content-type") || "", text: await response.text(), headers: Object.fromEntries(response.headers.entries()) };
}
function jsonOrNull(text) { try { return JSON.parse(text); } catch { return null; } }
function scriptSources(html, base) {
  const out = []; let pos = 0;
  while (true) {
    const a = html.toLowerCase().indexOf("<script", pos); if (a < 0) break;
    const b = html.indexOf(">", a); if (b < 0) break;
    const tag = html.slice(a, b + 1); const low = tag.toLowerCase(); const k = low.indexOf("src=");
    if (k >= 0) { const q = tag[k + 4]; if (q === "\"" || q === String.fromCharCode(39)) { const e = tag.indexOf(q, k + 5); if (e > k) { try { out.push(new URL(tag.slice(k + 5, e), base).href); } catch {} } } }
    pos = b + 1;
  }
  return [...new Set(out)];
}
async function browserCapture(urls, label) {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({ userAgent: UA, locale: "en-IN", viewport: { width: 1440, height: 1200 } });
  const page = await context.newPage();
  page.on("response", async response => {
    try {
      const request = response.request(); const url = response.url(); const ct = response.headers()["content-type"] || "";
      const interesting = request.resourceType() === "xhr" || request.resourceType() === "fetch" || ["api", "graphql", "product", "catalog", "search", "price", "inventory", "rome"].some(k => url.toLowerCase().includes(k));
      if (!interesting) return;
      let body = ""; if (ct.toLowerCase().includes("json") || ct.toLowerCase().includes("text")) { try { body = await response.text(); } catch {} }
      OUT.browser.push({ label, url, status: response.status(), method: request.method(), resourceType: request.resourceType(), contentType: ct, productish: productish(body), postData: trim(request.postData(), 7000), body: trim(body, 12000) });
    } catch {}
  });
  for (const url of urls) { try { await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }); await page.waitForTimeout(5000); } catch (e) { OUT.errors.push({ stage: "browser", label, url, error: String(e) }); } }
  await browser.close();
}

async function apple() {
  const pages = ["https://www.apple.com/in/shop/buy-iphone/iphone-17", "https://www.apple.com/in/shop/buy-iphone/iphone-17-pro"];
  for (const url of pages) {
    try {
      const r = await http(url, { headers: { accept: "text/html" } });
      const metricsStart = r.text.toLowerCase().indexOf("<script");
      const scriptCount = scriptSources(r.text, r.url).length;
      OUT.direct.push({ method: "page-source", url, status: r.status, contentType: r.contentType, bytes: r.text.length, scriptCount, hasProductSelectionBootstrap: r.text.includes("PRODUCT_SELECTION_BOOTSTRAP"), productish: productish(r.text), sample: trim(metricsStart >= 0 ? r.text.slice(0, 6000) : r.text, 6000) });
      for (const s of scriptSources(r.text, r.url).filter(x => ["step1", "buy", "product-locator", "commerce"].some(k => x.toLowerCase().includes(k))).slice(0, 40)) {
        try { const x = await http(s, { headers: { accept: "application/javascript,text/javascript,*/*" } }); const h = ["fulfillment", "inventory", "availability", "pricing", "product", "catalog", "sba", "api", "search"].filter(k => x.text.toLowerCase().includes(k)); if (h.length) OUT.direct.push({ method: "script-source", url: s, status: x.status, contentType: x.contentType, bytes: x.text.length, hints: h }); } catch (e) { OUT.errors.push({ stage: "apple-script", url: s, error: String(e) }); }
      }
    } catch (e) { OUT.errors.push({ stage: "apple-page", url, error: String(e) }); }
  }
  const candidates = [
    "https://www.apple.com/in/shop/search-services/suggestions/?query=iphone&locale=en_IN",
    "https://www.apple.com/search-services/suggestions/?query=iphone&src=globalnav&id=left-hunt-20260926&locale=en_IN",
    "https://www.apple.com/in/shop/sba/d/init",
    "https://www.apple.com/in/shop/sba/d/product-recommendations",
    "https://www.apple.com/in/shop/sba/availability-message",
    "https://www.apple.com/in/shop/api/kit-dimension-data"
  ];
  for (const url of candidates) {
    try { const r = await http(url, { headers: { accept: "application/json,text/plain,*/*", referer: pages[0] } }); const j = jsonOrNull(r.text); OUT.direct.push({ method: "candidate", url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, json: Boolean(j), productish: productish(r.text), qualifies: Boolean(j) && productish(r.text), sample: trim(r.text, 8000) }); } catch (e) { OUT.errors.push({ stage: "apple-candidate", url, error: String(e) }); }
  }
  await browserCapture(pages, "Apple");
  const q = OUT.direct.some(x => x.qualifies) || OUT.browser.some(x => x.productish && x.contentType.toLowerCase().includes("json"));
  OUT.qualification.push({ qualifies: q, note: "sitemap and embedded HTML/bootstrap data do not qualify" });
}

async function flipkart() {
  const makeBody = page => {
    const params = new URLSearchParams({ q: "laptop", otracker: "search", otracker1: "search", marketplace: "FLIPKART", "as-show": "on", as: "off" });
    if (page > 1) params.set("page", String(page));
    return { pageUri: "/search?" + params.toString(), pageContext: { fetchSeoData: true, paginatedFetch: false, pageNumber: page }, requestContext: { type: "BROWSE_PAGE" } };
  };
  const headers = { "accept": "*/*", "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7", "content-type": "application/json", "origin": "https://www.flipkart.com", "referer": "https://www.flipkart.com/", "user-agent": UA, "x-user-agent": UA + " FKUA/website/42/website/Desktop" };
  for (const endpoint of ["https://2.rome.api.flipkart.com/api/4/page/fetch", "https://www.flipkart.com/api/4/page/fetch"]) {
    for (const page of [1, 2]) {
      try {
        const r = await http(endpoint, { method: "POST", headers, body: JSON.stringify(makeBody(page)) });
        const j = jsonOrNull(r.text);
        const blob = j ? JSON.stringify(j) : r.text;
        OUT.direct.push({ method: "POST", endpoint, page, status: r.status, contentType: r.contentType, bytes: r.text.length, statusCode: j?.STATUS_CODE ?? null, productish: productish(blob), qualifies: Boolean(j) && productish(blob), sample: trim(r.text, 14000) });
      } catch (e) { OUT.errors.push({ stage: "flipkart-rome", endpoint, page, error: String(e) }); }
    }
  }
  await browserCapture(["https://www.flipkart.com/search?q=laptop", "https://www.flipkart.com/laptops/pr?sid=6bo,b5g"], "Flipkart");
  const q = OUT.direct.some(x => x.qualifies) || OUT.browser.some(x => x.productish && x.contentType.toLowerCase().includes("json"));
  OUT.qualification.push({ qualifies: q, note: "autosuggest and telemetry do not qualify" });
}

async function acer() {
  const body = { query: "query($search:String,$pageSize:Int=50,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages}items{sku name url_key}}}", variables: { search: "laptop", pageSize: 50, currentPage: 1 } };
  for (const url of ["https://store.acer.com/en-in/graphql", "https://store.acer.com/graphql"]) {
    try { const r = await http(url, { method: "POST", headers: { "content-type": "application/json", "accept": "application/json", "store": "default", "origin": "https://store.acer.com", "referer": "https://store.acer.com/en-in/" }, body: JSON.stringify(body) }); const j = jsonOrNull(r.text); OUT.direct.push({ method: "POST", url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, json: Boolean(j), productish: productish(r.text), qualifies: Boolean(j) && productish(r.text), sample: trim(r.text, 12000) }); } catch (e) { OUT.errors.push({ stage: "acer-graphql", url, error: String(e) }); }
  }
  for (const url of ["https://store.acer.com/en-in/", "https://store.acer.com/en-in/catalogsearch/result/?q=laptop"]) {
    try { const r = await http(url, { headers: { accept: "text/html" } }); OUT.direct.push({ method: "GET", url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, productish: productish(r.text), sample: trim(r.text, 5000) }); } catch (e) { OUT.errors.push({ stage: "acer-page", url, error: String(e) }); }
  }
  const q = OUT.direct.some(x => x.qualifies); OUT.qualification.push({ qualifies: q, note: "HTML is diagnostic only" });
}

if (TARGET === "Apple") await apple();
else if (TARGET === "Flipkart") await flipkart();
else if (TARGET === "Acer") await acer();
else throw new Error("Unknown TARGET=" + TARGET);

writeFileSync("left-targets-v2.json", JSON.stringify(OUT, null, 2));
console.log(JSON.stringify({ target: TARGET, direct: OUT.direct.length, browser: OUT.browser.length, errors: OUT.errors.length, qualification: OUT.qualification, qualifyingEndpoints: OUT.direct.filter(x => x.qualifies).map(x => x.url || x.endpoint) }, null, 2));