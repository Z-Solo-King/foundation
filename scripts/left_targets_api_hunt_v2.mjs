import { chromium } from "playwright";

const TARGET = process.env.TARGET || "";
const UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/153 Safari/537.36";

const OUT = { target: TARGET, direct: [], browser: [], errors: [], qualification: [] };

function trim(value, max = 9000) { return String(value ?? "").slice(0, max); }
function hasProductData(text) {
  const t = String(text ?? "").toLowerCase();
  return ["product","products","sku","price","sellingprice","finalprice","mrp","listingid","productid","items"].filter(k => t.includes(k)).length >= 2;
}
async function fetchAny(url, options = {}) {
  const response = await fetch(url, {
    redirect: "follow",
    headers: { "user-agent": UA, "accept": "*/*", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  return { url: response.url, status: response.status, contentType: response.headers.get("content-type") || "", text, headers: Object.fromEntries(response.headers.entries()) };
}

async function apple() {
  const pages = [
    "https://www.apple.com/in/shop/buy-iphone/iphone-17",
    "https://www.apple.com/in/shop/buy-iphone/iphone-17-pro",
  ];
  for (const url of pages) {
    try {
      const r = await fetchAny(url, { headers: { accept: "text/html" } });
      const scriptSrcs = [...r.text.matchAll(/<script\\b[^>]+src=["\']([^"\']+)["\']/gi)].map(m => new URL(m[1], r.url).href);
      const metrics = r.text.match(/<script[^>]+id=["\']metrics["\'][^>]*>([\\s\\S]*?)<\\/script>/i)?.[1] || "";
      const bootstrap = r.text.includes("PRODUCT_SELECTION_BOOTSTRAP");
      OUT.direct.push({ method: "page-source", url, status: r.status, contentType: r.contentType, bytes: r.text.length, embeddedMetrics: Boolean(metrics), embeddedBootstrap: bootstrap, productish: hasProductData(metrics || r.text), sample: trim(metrics || r.text, 6000) });
      for (const s of scriptSrcs.filter(x => /step1|buyflow|commerce|product|fulfill|inventory|catalog|search/i.test(x)).slice(0, 40)) {
        try {
          const x = await fetchAny(s, { headers: { accept: "application/javascript,text/javascript,*/*" } });
          const hints = x.text.split(/\\r?\\n/).filter(line => /fulfillment|inventory|availability|catalog|product|price|api|graphql|search/i.test(line)).slice(0, 80);
          if (hints.length) OUT.direct.push({ method: "script-source", url: s, status: x.status, contentType: x.contentType, bytes: x.text.length, productish: hasProductData(x.text), hints: hints.map(v => trim(v, 700)) });
        } catch (e) { OUT.errors.push({ stage: "apple-script", url: s, error: String(e) }); }
      }
    } catch (e) { OUT.errors.push({ stage: "apple-page", url, error: String(e) }); }
  }
  const directCandidates = [
    "https://www.apple.com/in/shop/search?query=iphone&format=json",
    "https://www.apple.com/in/shop/search?query=iphone&output=json",
    "https://www.apple.com/in/shop/products.json",
    "https://www.apple.com/in/shop/catalog.json",
    "https://www.apple.com/in/shop/sba/d/init",
    "https://www.apple.com/in/shop/sba/d/product-recommendations",
    "https://www.apple.com/in/shop/sba/availability-message",
    "https://www.apple.com/in/shop/api/kit-dimension-data",
  ];
  for (const url of directCandidates) {
    try {
      const r = await fetchAny(url, { headers: { accept: "application/json,text/plain,*/*", referer: pages[0] } });
      const qualify = /json|xml/i.test(r.contentType) && hasProductData(r.text);
      OUT.direct.push({ method: "direct-candidate", url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, productish: hasProductData(r.text), qualifies: qualify, sample: trim(r.text) });
    } catch (e) { OUT.errors.push({ stage: "apple-direct", url, error: String(e) }); }
  }
  try {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ userAgent: UA, locale: "en-IN", viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    page.on("response", async response => {
      try {
        const request = response.request();
        const url = response.url();
        const ct = response.headers()["content-type"] || "";
        if (!/xhr|fetch/i.test(request.resourceType()) && !/graphql|api|product|catalog|price|inventory|fulfill|search/i.test(url)) return;
        let body = "";
        if (/json|text|javascript/i.test(ct) && response.status() < 500) { try { body = await response.text(); } catch {} }
        OUT.browser.push({ url, status: response.status(), method: request.method(), resourceType: request.resourceType(), contentType: ct, productish: hasProductData(body), body: trim(body, 10000), postData: trim(request.postData(), 5000) });
      } catch {}
    });
    for (const url of pages) { try { await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }); await page.waitForTimeout(5000); } catch (e) { OUT.errors.push({ stage: "apple-browser", url, error: String(e) }); } }
    await browser.close();
  } catch (e) { OUT.errors.push({ stage: "apple-browser-launch", error: String(e) }); }
  OUT.qualification = [{ rule: "direct-api-or-product-feed-only", qualifies: OUT.direct.some(x => x.qualifies) || OUT.browser.some(x => x.productish && /json|xml/i.test(x.contentType || "")), note: "embedded metrics/bootstrap and URL sitemaps do not qualify" }];
}

async function flipkart() {
  const bodyFor = (page, type = "BROWSE_PAGE") => {
    const params = new URLSearchParams({ q: "laptop", otracker: "search", otracker1: "search", marketplace: "FLIPKART", "as-show": "on", as: "off" });
    if (page > 1) params.set("page", String(page));
    return {
      pageUri: "/search?" + params.toString(),
      pageContext: { fetchSeoData: true, paginatedFetch: false, pageNumber: page },
      requestContext: { type },
    };
  };
  const headers = { "accept": "*/*", "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7", "content-type": "application/json", "origin": "https://www.flipkart.com", "referer": "https://www.flipkart.com/", "user-agent": UA, "x-user-agent": UA + " FKUA/website/42/website/Desktop" };
  for (const endpoint of ["https://2.rome.api.flipkart.com/api/4/page/fetch", "https://www.flipkart.com/api/4/page/fetch"]) {
    for (const page of [1, 2]) {
      try {
        const r = await fetchAny(endpoint, { method: "POST", headers, body: JSON.stringify(bodyFor(page)) });
        OUT.direct.push({ endpoint, page, status: r.status, contentType: r.contentType, bytes: r.text.length, productish: hasProductData(r.text), statusCode: (() => { try { return JSON.parse(r.text)?.STATUS_CODE ?? null; } catch { return null; } })(), sample: trim(r.text, 12000) });
      } catch (e) { OUT.errors.push({ stage: "flipkart-direct", endpoint, page, error: String(e) }); }
    }
  }
  try {
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ userAgent: UA, locale: "en-IN", viewport: { width: 1440, height: 1200 } });
    const page = await context.newPage();
    page.on("response", async response => {
      try { const request = response.request(), url = response.url(), ct = response.headers()["content-type"] || ""; if (!/xhr|fetch/i.test(request.resourceType()) && !/rome|api|search|product/i.test(url)) return; let body = ""; if (/json|text/i.test(ct) && response.status() < 500) { try { body = await response.text(); } catch {} } OUT.browser.push({ url, status: response.status(), method: request.method(), resourceType: request.resourceType(), contentType: ct, productish: hasProductData(body), body: trim(body, 10000), postData: trim(request.postData(), 7000) }); } catch {}
    });
    for (const url of ["https://www.flipkart.com/search?q=laptop", "https://www.flipkart.com/laptops/pr?sid=6bo,b5g"]) { try { await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 }); await page.waitForTimeout(7000); await page.mouse.wheel(0, 12000); await page.waitForTimeout(4000); } catch (e) { OUT.errors.push({ stage: "flipkart-browser", url, error: String(e) }); } }
    await browser.close();
  } catch (e) { OUT.errors.push({ stage: "flipkart-browser-launch", error: String(e) }); }
  const productApi = OUT.direct.some(x => x.productish && /json/i.test(x.contentType)) || OUT.browser.some(x => x.productish && /json/i.test(x.contentType));
  OUT.qualification = [{ rule: "direct-api-or-product-feed-only", qualifies: productApi, note: "autosuggest/telemetry alone do not qualify" }];
}

async function acer() {
  const gql = { query: "query($search:String,$pageSize:Int=50,$currentPage:Int=1){products(search:$search,pageSize:$pageSize,currentPage:$currentPage){total_count page_info{current_page page_size total_pages}items{sku name url_key}}}", variables: { search: "laptop", pageSize: 50, currentPage: 1 } };
  for (const url of ["https://store.acer.com/en-in/graphql", "https://store.acer.com/graphql"]) {
    try {
      const r = await fetchAny(url, { method: "POST", headers: { "content-type": "application/json", "accept": "application/json", "store": "default", "origin": "https://store.acer.com", "referer": "https://store.acer.com/en-in/" }, body: JSON.stringify(gql) });
      OUT.direct.push({ url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, productish: hasProductData(r.text), sample: trim(r.text, 12000) });
    } catch (e) { OUT.errors.push({ stage: "acer-graphql", url, error: String(e) }); }
  }
  for (const url of ["https://store.acer.com/en-in/", "https://store.acer.com/en-in/catalogsearch/result/?q=laptop"]) {
    try {
      const r = await fetchAny(url, { headers: { accept: "text/html" } });
      OUT.direct.push({ url: r.url, status: r.status, contentType: r.contentType, bytes: r.text.length, productish: hasProductData(r.text), sample: trim(r.text, 4000) });
    } catch (e) { OUT.errors.push({ stage: "acer-page", url, error: String(e) }); }
  }
  OUT.qualification = [{ rule: "direct-api-or-product-feed-only", qualifies: OUT.direct.some(x => x.productish && /json|xml/i.test(x.contentType)), note: "HTML fallback is diagnostic only" }];
}

if (TARGET === "Apple") await apple();
else if (TARGET === "Flipkart") await flipkart();
else if (TARGET === "Acer") await acer();
else throw new Error(`Unknown TARGET=${TARGET}`);

console.log(JSON.stringify({ target: OUT.target, direct: OUT.direct.length, browser: OUT.browser.length, errors: OUT.errors.length, qualification: OUT.qualification }, null, 2));
writeFileSync("left-targets-v2.json", JSON.stringify(OUT, null, 2));