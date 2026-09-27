import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, writeFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const execFileAsync = promisify(execFile);

const TARGETS = [
  ["ithunt","https://ithunt.in"],
  ["kccomputers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Moskeys","https://moskeys.com"],
  ["Theproaudio","https://www.theproaudio.com"],
];

const PATHS = [
  "/",
  "/robots.txt",
  "/sitemap.xml",
  "/wp-sitemap.xml",
  "/wp-json/",
  "/wp-json/wc/store/v1/products",
  "/wp-json/wc/store/v1/products?per_page=3",
  "/?rest_route=/wc/store/v1/products&per_page=3",
  "/google.xml",
  "/google-products.xml",
  "/google-product-feed.xml",
  "/google-shopping.xml",
  "/google-shopping-feed.xml",
  "/merchant-feed.xml",
  "/feed/google.xml",
  "/feeds/google.xml",
  "/product-feed.xml",
  "/products-feed.xml",
  "/feed.xml",
  "/rss.xml",
  "/products.rss",
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-content/uploads/woo-feed/google/xml/google.xml",
  "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/wppfm-feeds/google.xml",
  "/wp-json/feedcraft-product-feed/v1/xml",
];

const UAS = {
  chrome_desktop: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36",
  firefox_desktop: "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0",
  safari_desktop: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
  verifier: "FoundationFeedVerifier/1.0 (+public; no-browser-bypass)",
};

function classify(status, headers, body) {
  const h = Object.fromEntries([...headers.entries()].map(([k,v]) => [k.toLowerCase(), v]));
  const b = String(body || "").slice(0, 20000).toLowerCase();
  const signals = [];
  if (h.server) signals.push("server=" + h.server);
  if (h["cf-ray"]) signals.push("cf-ray");
  if (h["cf-cache-status"]) signals.push("cf-cache-status=" + h["cf-cache-status"]);
  if (h["x-powered-by"]) signals.push("x-powered-by=" + h["x-powered-by"]);
  if (h["x-turbo-charged-by"]) signals.push("x-turbo-charged-by=" + h["x-turbo-charged-by"]);
  if (h["x-sucuri-id"]) signals.push("x-sucuri-id");
  if (/just a moment|cf-chl-|challenge-platform|attention required|cloudflare/i.test(b)) signals.push("cloudflare/challenge-text");
  if (/wordfence/i.test(b) || h["x-wordfence"]) signals.push("wordfence");
  if (/sucuri/i.test(b)) signals.push("sucuri");
  if (/mod_security|modsecurity/i.test(b)) signals.push("modsecurity");
  if (/forbidden|access denied|request blocked/i.test(b)) signals.push("access-denied-text");
  return { status, signals };
}

async function probeFetch(url, ua) {
  const ac = new AbortController();
  const timer = setTimeout(() => ac.abort(), 12000);
  try {
    const r = await fetch(url, {
      redirect: "follow",
      signal: ac.signal,
      headers: {
        "User-Agent": ua,
        "Accept": "application/json,application/xml,application/rss+xml,text/xml,text/html;q=0.9,*/*;q=0.2",
      },
    });
    const buf = Buffer.from(await r.arrayBuffer());
    const body = buf.length <= 2 * 1024 * 1024 ? buf.toString("utf8") : "";
    const meta = classify(r.status, r.headers, body);
    return {
      ok: true, status: r.status, final_url: r.url, bytes: buf.length,
      content_type: r.headers.get("content-type"),
      location: r.headers.get("location"),
      server: r.headers.get("server"),
      cf_ray: r.headers.get("cf-ray"),
      cf_cache_status: r.headers.get("cf-cache-status"),
      x_powered_by: r.headers.get("x-powered-by"),
      x_turbo_charged_by: r.headers.get("x-turbo-charged-by"),
      sample_sha256: createHash("sha256").update(buf.subarray(0, Math.min(buf.length, 65536))).digest("hex"),
      sample: body.slice(0, 300).replace(/\s+/g, " "),
      ...meta,
      transport: "fetch",
    };
  } catch (e) {
    return { ok: false, error: e?.name || String(e), transport: "fetch" };
  } finally { clearTimeout(timer); }
}

async function probeCurl(url, ua, httpVersion) {
  try {
    const args = [
      "-sS","-L","-4","--connect-timeout","6","--max-time","15","-A",ua,
      httpVersion === "2" ? "--http2" : "--http1.1",
      "-H","Accept: application/json,application/xml,application/rss+xml,text/xml,text/html;q=0.9,*/*;q=0.2",
      "-w","\n__STATUS__%{http_code}\n__URL__%{url_effective}\n__SERVER__%{header{server}}\n__CFRAY__%{header{cf-ray}}\n__CFSTATUS__%{header{cf-cache-status}}\n__TYPE__%{content_type}\n",
      url,
    ];
    const { stdout } = await execFileAsync("curl", args, { timeout: 18000, maxBuffer: 8 * 1024 * 1024 });
    const text = String(stdout || "");
    const pos = text.lastIndexOf("__STATUS__");
    if (pos < 0) return { ok:false, error:"NO_MARKERS", transport:"curl-http"+httpVersion };
    const cut = text.slice(0, pos).replace(/\n$/, "");
    const field = name => {
      const marker = "__"+name;
      const p = text.lastIndexOf(marker, pos);
      if (p < 0) return "";
      const start = p + marker.length;
      const end = text.indexOf("\n", start);
      return end < 0 ? "" : text.slice(start, end).trim();
    };
    const status = Number(field("STATUS"));
    const metaHeaders = new Headers();
    if (field("SERVER")) metaHeaders.set("server", field("SERVER"));
    if (field("CFRAY")) metaHeaders.set("cf-ray", field("CFRAY"));
    if (field("CFSTATUS")) metaHeaders.set("cf-cache-status", field("CFSTATUS"));
    const meta = classify(status, metaHeaders, cut);
    return {
      ok:true, status, final_url:field("URL"), bytes:Buffer.byteLength(cut),
      content_type:field("TYPE"), server:field("SERVER") || null, cf_ray:field("CFRAY") || null,
      cf_cache_status:field("CFSTATUS") || null,
      sample_sha256:createHash("sha256").update(Buffer.from(cut).subarray(0,65536)).digest("hex"),
      sample:cut.slice(0,300).replace(/\s+/g," "),
      ...meta, transport:"curl-http"+httpVersion,
    };
  } catch (e) {
    return { ok:false, error:e?.code || e?.name || String(e), transport:"curl-http"+httpVersion };
  }
}

async function dns(host) {
  try {
    const a = await execFileAsync("dig", ["+short", "A", host], {timeout:6000});
    const aaaa = await execFileAsync("dig", ["+short", "AAAA", host], {timeout:6000});
    const ns = await execFileAsync("dig", ["+short", "NS", host], {timeout:6000});
    return {a:a.stdout.trim().split(/\s+/).filter(Boolean), aaaa:aaaa.stdout.trim().split(/\s+/).filter(Boolean), ns:ns.stdout.trim().split(/\s+/).filter(Boolean)};
  } catch (e) { return {error:e?.message || String(e)}; }
}

const results = [];
for (const [name, base] of TARGETS) {
  const host = new URL(base).hostname;
  const row = {name, base, dns:await dns(host), probes:[]};
  for (const path of PATHS) {
    const url = new URL(path, base + "/").href;
    for (const [uaName, ua] of Object.entries(UAS)) {
      const f = await probeFetch(url, ua);
      row.probes.push({path,ua:uaName,...f});
      if (f.ok && f.status === 200 && path.includes("wc/store/v1/products") && f.bytes > 0) break;
    }
    const c1 = await probeCurl(url, UAS.verifier, "1.1");
    row.probes.push({path,ua:"verifier",...c1});
    const c2 = await probeCurl(url, UAS.verifier, "2");
    row.probes.push({path,ua:"verifier",...c2});
  }
  results.push(row);
  console.log(JSON.stringify({
    name,
    dns: row.dns,
    root: row.probes.filter(p=>p.path === "/" && p.transport === "fetch").map(p=>({ua:p.ua,status:p.status,error:p.error,signals:p.signals,server:p.server,cf_ray:p.cf_ray})),
    api: row.probes.filter(p=>p.path === "/wp-json/wc/store/v1/products" && p.transport === "fetch").map(p=>({ua:p.ua,status:p.status,error:p.error,signals:p.signals,server:p.server,cf_ray:p.cf_ray})),
    successes: row.probes.filter(p=>p.status === 200 && /xml|feed|merchant|google|shopping|product/i.test(p.path)).slice(0,10).map(p=>({path:p.path,ua:p.ua,transport:p.transport,status:p.status,bytes:p.bytes,signals:p.signals})),
  }, null, 2));
}

await mkdir("out/1247-transport-diagnostic",{recursive:true});
await writeFile("out/1247-transport-diagnostic/results.json", JSON.stringify({
  generated_at:new Date().toISOString(),
  target_count:results.length,
  results,
}, null, 2) + "\n");
