#!/usr/bin/env node
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const FAMILY_PATTERNS = {
  woocommerce_google_product_feed: [
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=2500",
    "/?woocommerce_gpf=google&gpf_start=100&gpf_limit=100",
    "/?woocommerce_gpf=google&gpf_start=500&gpf_limit=500",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000"
  ],
  ctx_feed_webappick: [
    "/?woo_feed=google&wt=xml",
    "/?woo_feed=google-shopping&wt=xml",
    "/?woo_feed=google_shopping&wt=xml",
    "/?woo_feed=google-products&wt=xml",
    "/?woo_feed=google_product_feed&wt=xml",
    "/?woo_feed=google-feed&wt=xml",
    "/?woo_feed=google_feed&wt=xml",
    "/?woo_feed=google-merchant&wt=xml",
    "/?woo_feed=google_merchant&wt=xml",
    "/?woo_feed=gmc&wt=xml",
    "/?woo_feed=googlebase&wt=xml",
    "/?woo_feed=product-feed&wt=xml",
    "/?woo_feed=listings&wt=xml",
    "/?woo_feed=listings07&wt=xml",
    "/?woo_feed=merchantcenter&wt=xml",
    "/?woo_feed=merchantcenter2&wt=xml",
    "/?woo_feed=products&wt=xml",
    "/?woo_feed=google",
    "/?woo_feed=google-shopping",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/google_shopping_ctx_1.xml",
    "/wp-content/uploads/woo-feed/google/xml/google_shopping_ctx_1-3.xml",
    "/wp-content/uploads/woo-feed/google/xml/listings.xml",
    "/wp-content/uploads/woo-feed/google/xml/listings07.xml",
    "/wp-content/uploads/woo-feed/google/xml/merchantcenter2.xml",
    "/wp-content/uploads/woo-feed/google/xml/feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/googleshoplb24a.xml"
  ],
  adtribes_product_feed_pro: [
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/google-shopping.xml"
  ],
  wpfm_product_feed_manager: [
    "/wp-content/uploads/wppfm-feeds/Google.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Products.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Products-New.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Products-1.xml",
    "/wp-content/uploads/wppfm-feeds/Google_Products.xml",
    "/wp-content/uploads/wppfm-feeds/Google_Product.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Feed.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Feed_1.xml",
    "/wp-content/uploads/wppfm-feeds/GoogleFeed.xml",
    "/wp-content/uploads/wppfm-feeds/google-feed.xml",
    "/wp-content/uploads/wppfm-feeds/google-products-feed.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Shopping.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Shopping-Feed.xml",
    "/wp-content/uploads/wppfm-feeds/feed-google.xml",
    "/wp-content/uploads/wppfm-feeds/feed-google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/Google_mar_2018.xml",
    "/wp-content/uploads/wppfm-feeds/feed.xml"
  ],
  webtoffee_product_feed: [
    "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_gmc_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_products_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_fb_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/google.xml",
    "/wp-content/uploads/webtoffee_product_feed/google-shopping.xml",
    "/wp-content/uploads/webtoffee_product_feed/google-product-feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/google-shopping-feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/feed.xml"
  ],
  codesolz_merchant_feed_booster: [
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-shopping.xml"
  ],
  feedcraft: [
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/google",
    "/wp-json/feedcraft-product-feed/v1/feed.xml"
  ],
  rexfed_product_feed: [
    "/wp-content/uploads/rex-feed/feed-1.xml",
    "/wp-content/uploads/rex-feed/feed-687.xml",
    "/wp-content/uploads/rex-feed/feed-15364.xml",
    "/wp-content/uploads/rex-feed/feed-546616.xml",
    "/wp-content/uploads/rex-feed/feed-3428.xml",
    "/wp-content/uploads/rex-feed/feed-318303.xml",
    "/wp-content/uploads/rex-feed/feed-3035.xml",
    "/wp-content/uploads/rex-feed/feed-77723.xml",
    "/wp-content/uploads/rex-feed/google.xml",
    "/wp-content/uploads/rex-feed/google-feed.xml",
    "/wp-content/uploads/rex-feed/google-product-feed.xml",
    "/wp-content/uploads/rex-feed/google-shopping.xml"
  ],
  klpsoft_feeds: [
    "/wp-content/uploads/klp-feeds-xml/google.xml",
    "/wp-content/uploads/klp-feeds-xml/google-feed.xml",
    "/wp-content/uploads/klp-feeds-xml/google-shopping.xml",
    "/wp-content/uploads/klp-feeds-xml/google-merchant.xml",
    "/wp-content/uploads/klp-feeds-xml/gmc.xml",
    "/wp-content/uploads/klp-feeds-xml/feed.xml"
  ],
  icopydoc_gmc: [
    "/wp-content/uploads/feed-xml-0.xml",
    "/wp-content/uploads/feed-xml-1.xml",
    "/wp-content/uploads/feed-xml-2.xml",
    "/wp-content/uploads/feed-xml-3.xml"
  ]
};

const GENERIC = [
  "/google.xml",
  "/google-feed.xml",
  "/google-products.xml",
  "/google-product-feed.xml",
  "/google-shopping.xml",
  "/google-shopping-feed.xml",
  "/google-merchant.xml",
  "/google-merchant-feed.xml",
  "/merchant.xml",
  "/merchant-feed.xml",
  "/product-feed.xml",
  "/products-feed.xml",
  "/feed.xml",
  "/gpf.xml",
  "/googlebase.xml",
  "/google_base.xml",
  "/google_shopping.xml"
];

const GENERIC_BY_DIR = [
  ["/wp-content/uploads/woo-feed/google/xml/", ["google.xml","google-shopping.xml","google-shopping-feed.xml","google_shopping_ctx_1.xml","google_shopping_ctx_1-3.xml","listings.xml","listings07.xml","merchantcenter2.xml","feed.xml","googleshoplb24a.xml"]],
  ["/wp-content/uploads/woo-product-feed-pro/xml/", ["google.xml","google-shopping.xml","google-shopping-feed.xml","google-products.xml","google-product-feed.xml","feed.xml"]],
  ["/wp-content/uploads/wppfm-feeds/", ["Google.xml","Google-Products.xml","Google-Products-New.xml","Google-Products-1.xml","Google-Feed.xml","Google-Feed_1.xml","Google-Shopping.xml","Google-Shopping-Feed.xml","google-feed.xml","google-products-feed.xml","feed-google.xml","feed.xml"]],
  ["/wp-content/uploads/webtoffee_product_feed/", ["google.xml","google-feed.xml","wt_google_Feed.xml","wt_gs_Feed.xml","wt_gmc_Feed.xml","wt_google_products_Feed.xml","wt_google_shopping_Feed.xml","wt_fb_Feed.xml","feed.xml"]],
  ["/wp-content/uploads/codesolz-feeds/", ["google-products.xml","google.xml","google-shopping.xml"]],
  ["/wp-content/uploads/rex-feed/", ["feed-1.xml","feed-687.xml","feed-15364.xml","feed-546616.xml","feed-3428.xml","feed-318303.xml","feed-3035.xml","feed-77723.xml","google.xml","google-feed.xml"]],
  ["/wp-content/uploads/klp-feeds-xml/", ["google.xml","google-feed.xml","google-shopping.xml","google-merchant.xml","gmc.xml","feed.xml"]],
  ["/wp-content/uploads/", ["feed-xml-0.xml","feed-xml-1.xml","feed-xml-2.xml","feed-xml-3.xml"]]
];

const CHALLENGE_MARKERS = [
  "just a moment","cf-chl-","cf-turnstile","cf-browser-verification",
  "challenge-platform","captcha","access denied","attention required",
  "checking your browser","request blocked","verify you are human"
];

const UA = "Mozilla/5.0 (compatible; WooCommercePluginFamilyGuess/4.0.1)";
const MAX_BODY = 12 * 1024 * 1024;

function sameHost(a, b) {
  try {
    const ah = new URL(a).hostname.toLowerCase().replace(/^www\./, "");
    const bh = new URL(b).hostname.toLowerCase().replace(/^www\./, "");
    return ah === bh;
  } catch {
    return false;
  }
}

function canonicalize(root, raw) {
  const u = new URL(raw, root);
  if (!/^https?:$/.test(u.protocol) || !sameHost(u.href, root)) throw new Error("invalid_or_cross_host");
  u.hash = "";
  return u.href;
}

function strictValidate(body) {
  if (!body) return { valid:false, reason:"empty" };
  const text = String(body);
  const low = text.toLowerCase();
  const head = low.slice(0, 30000);
  if (CHALLENGE_MARKERS.some(m => head.includes(m))) return { valid:false, reason:"challenge_or_access_denied" };
  if (/^\s*<(?:urlset|sitemapindex)\b/i.test(text)) return { valid:false, reason:"sitemap" };
  if (!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(text)) return { valid:false, reason:"not_xml" };
  if (!/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(text)) return { valid:false, reason:"no_google_namespace" };
  const blocks = [];
  for (const m of text.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi)) blocks.push(m[1]);
  for (const m of text.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)) blocks.push(m[1]);
  if (!blocks.length) return { valid:false, reason:"no_item_or_entry" };
  const required = ["id","title","link","price"];
  let validItems = 0;
  for (const block of blocks) {
    if (required.every(f => new RegExp("<g:" + f + "\\\\b[^>]*>[\\\\s\\\\S]*?<\\\\/g:" + f + ">", "i").test(block))) validItems++;
  }
  if (!validItems) return { valid:false, reason:"no_item_with_core_google_fields", items:blocks.length, valid_items:0 };
  return { valid:true, reason:"validated_google_merchant_xml", items:blocks.length, valid_items:validItems };
}

function identityTokens(site) {
  const host = new URL(site.root).hostname.replace(/^www\./i, "").split(".")[0];
  return [...new Set([host, site.site])]
    .flatMap(v => String(v).toLowerCase().split(/[^a-z0-9]+/).filter(Boolean))
    .filter(v => v.length >= 3 && v.length <= 28)
    .slice(0, 8);
}

function addCandidate(map, root, raw, rank, source, family) {
  try {
    const url = canonicalize(root, raw);
    const old = map.get(url);
    if (!old || rank > old.rank) map.set(url, { url, rank, source, family });
  } catch {}
}

function candidatesFor(site) {
  const family = site.family;
  const map = new Map();
  const add = (raw, rank, source, fam = family) => addCandidate(map, site.root, raw, rank, source, fam);
  const addFileWithCache = (raw, rank, source, fam = family) => {
    add(raw, rank, source, fam);
    if (/\.(?:xml|xml\.gz)$/i.test(raw)) {
      add(raw + "?q=1", rank - 1, source + "_cache_bust", fam);
    }
  };

  if (family === "google_for_woocommerce") return { candidates:[], reason:"api_integrated_family" };

  if (family !== "unknown_woocommerce" && FAMILY_PATTERNS[family]) {
    for (const raw of FAMILY_PATTERNS[family]) {
      if (raw.startsWith("/wp-content/uploads/")) addFileWithCache(raw, 220, "documented-family");
      else add(raw, 220, "documented-family");
    }
    if (family === "ctx_feed_webappick") {
      const names = ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase","product-feed","products","listings","listings07","merchantcenter","merchantcenter2"];
      for (const n of names) add("/?woo_feed=" + n + "&wt=xml", 205, "ctx-semantic-query", family);
    }
    if (family === "webtoffee_product_feed") {
      for (const raw of [
        "wt_google_Feed.xml","wt_gs_Feed.xml","wt_gmc_Feed.xml","wt_google_products_Feed.xml",
        "wt_google_shopping_Feed.xml","wt_google_shopping_feed.xml","google.xml","google-shopping.xml",
        "google-product-feed.xml","google-shopping-feed.xml","feed.xml"
      ]) addFileWithCache("/wp-content/uploads/webtoffee_product_feed/" + raw, 205, "webtoffee-semantic-name", family);
    }
    if (family === "wpfm_product_feed_manager") {
      for (const token of identityTokens(site)) {
        for (const n of ["google.xml","google-feed.xml","google-products.xml","google-product-feed.xml","google-shopping.xml"]) {
          addFileWithCache("/wp-content/uploads/wppfm-feeds/" + token + "-" + n, 125, "identity-semantic-name", family);
        }
      }
    }
    return {
      candidates: [...map.values()].sort((a,b) => b.rank - a.rank || a.url.localeCompare(b.url)).slice(0, 140)
    };
  }

  for (const [fam, patterns] of Object.entries(FAMILY_PATTERNS)) {
    for (const raw of patterns) {
      if (raw.startsWith("/wp-content/uploads/")) addFileWithCache(raw, 190, "cross-family-documented", fam);
      else add(raw, 190, "cross-family-documented", fam);
    }
  }
  for (const [dir, names] of GENERIC_BY_DIR) {
    for (const n of names) addFileWithCache(dir + n, 120, "cross-family-directory", "directory");
  }
  for (const raw of GENERIC) addFileWithCache(raw, 105, "root-generic", "generic");
  for (const n of ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_merchant","gmc","googlebase","listings","listings07","merchantcenter2","products"]) {
    add("/?woo_feed=" + n + "&wt=xml", 110, "cross-family-ctx-query", "ctx_feed_webappick");
    add("/?woo_feed=" + n, 108, "cross-family-ctx-query-no-format", "ctx_feed_webappick");
    add("/?woocommerce_gpf=" + n, 100, "cross-family-gpf-query", "woocommerce_google_product_feed");
  }
  return {
    candidates: [...map.values()]
      .sort((a,b) => b.rank - a.rank || a.url.localeCompare(b.url))
      .slice(0, 96)
  };
}

async function fetchCandidate(url, timeoutMs, attempts) {
  let last = { status:0, final_url:url, transport:"request_error", challenge:false, validation:{valid:false,reason:"request_error"} };
  for (let attempt = 1; attempt <= attempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const r = await fetch(url, {
        redirect:"follow",
        headers:{
          "user-agent":UA,
          "accept":"application/xml,text/xml,application/rss+xml,*/*;q=0.1",
          "cache-control":"no-cache"
        },
        signal:controller.signal
      });
      let data = Buffer.from(await r.arrayBuffer());
      if (data.length >= 2 && data[0] === 0x1f && data[1] === 0x8b) {
        try { data = gunzipSync(data); } catch {
          last = { status:r.status, final_url:r.url || url, transport:"invalid_gzip", challenge:false, validation:{valid:false,reason:"invalid_gzip"} };
          break;
        }
      }
      const finalUrl = r.url || url;
      const body = data.toString("utf8").slice(0, MAX_BODY);
      const challenge = CHALLENGE_MARKERS.some(m => body.slice(0,30000).toLowerCase().includes(m));
      const validation = (r.status === 200 && sameHost(finalUrl, url)) ? strictValidate(body) : {valid:false,reason:"http_or_redirect"};
      last = { status:r.status, final_url:finalUrl, transport:r.ok ? "public_http" : "http_error", challenge, validation };
      if (validation.valid) return last;
      if (![429,502,503,504].includes(r.status)) return last;
      const ra = Number.parseInt(r.headers.get("retry-after") || "", 10);
      await delay(Number.isFinite(ra) ? Math.min(ra * 1000, 5000) : attempt * 900);
    } catch (e) {
      last = { status:0, final_url:url, transport:e?.name === "AbortError" ? "timeout" : "request_error", challenge:false, validation:{valid:false,reason:e?.name === "AbortError" ? "timeout" : "request_error"} };
      if (attempt < attempts) await delay(attempt * 500);
    } finally {
      clearTimeout(timer);
    }
  }
  return last;
}

async function mapPool(items, concurrency, fn) {
  const out = new Array(items.length);
  let next = 0;
  async function worker() {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      out[i] = await fn(items[i], i);
    }
  }
  await Promise.all(Array.from({length:Math.max(1,concurrency)}, worker));
  return out;
}

async function runOne(site, cfg) {
  const generated = candidatesFor(site);
  if (generated.reason === "api_integrated_family") {
    return {
      site:site.site, root:site.root, family:site.family, evidence:site.evidence,
      guessing_mode:"skipped_api_integrated_family", candidate_count:0, candidate_hits:[],
      status:"API_INTEGRATED_NO_XML_GUESS", transport_summary:{}
    };
  }
  const candidates = generated.candidates;
  const results = await mapPool(candidates, cfg.candidateConcurrency, c => fetchCandidate(c.url, cfg.timeoutMs, cfg.attempts).then(r => ({...c,...r})));
  const hits = results.filter(x => x.validation.valid && sameHost(x.final_url, site.root));
  return {
    site:site.site, root:site.root, family:site.family, evidence:site.evidence,
    guessing_mode:site.family === "unknown_woocommerce" ? "bounded_cross_family" : "family_specific",
    candidate_count:candidates.length,
    candidate_hits:hits.slice(0,10),
    status:hits.length ? "NATIVE_FEED_VERIFIED" :
      (results.some(x => x.status === 403 || x.status === 429 || x.transport === "timeout" || x.challenge)
        ? "NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED" : "NO_NATIVE_FEED_VERIFIED"),
    transport_summary:{
      http_200:results.filter(x => x.status === 200).length,
      http_403:results.filter(x => x.status === 403).length,
      http_404:results.filter(x => x.status === 404).length,
      http_429:results.filter(x => x.status === 429).length,
      timeouts:results.filter(x => x.transport === "timeout").length,
      challenges:results.filter(x => x.challenge).length
    },
    top_misses:results
      .filter(x => x.status === 200 || x.status === 403 || x.status === 429 || x.transport === "timeout")
      .slice(0,25)
      .map(x => ({family:x.family,url:x.url,status:x.status,reason:x.validation.reason,final_url:x.final_url}))
  };
}

async function main() {
  const args = process.argv.slice(2);
  const getArg = k => args.includes(k) ? args[args.indexOf(k) + 1] : undefined;
  const input = getArg("--input") || "docs/feed-lab/WOOCOMMERCE_PLUGIN_FAMILY_GUESS_MANIFEST_2026-09-30.json";
  const outDir = getArg("--out") || "out/woocommerce-plugin-family-guess-v4";
  const shard = Number(getArg("--shard") || process.env.SHARD || 1);
  const shards = Number(getArg("--shards") || process.env.SHARDS || 6);
  const candidateConcurrency = Math.max(1, Number(getArg("--candidate-concurrency") || process.env.CANDIDATE_CONCURRENCY || 6));
  const timeoutMs = Math.max(1500, Number(getArg("--timeout-ms") || process.env.REQUEST_TIMEOUT_MS || 6500));
  const attempts = Math.max(1, Number(getArg("--attempts") || process.env.ATTEMPTS || 2));
  const matrix = JSON.parse(await readFile(input, "utf8"));
  const selected = matrix.sites.filter((_,i) => i % shards + 1 === shard);
  await mkdir(outDir, {recursive:true});
  const results = await mapPool(selected, 1, site => runOne(site, {candidateConcurrency, timeoutMs, attempts}));
  const payload = {
    schema:"woocommerce-plugin-family-guess-v4/v2",
    strategy:"plugin-family-specific-xml-guess-only",
    shard, shards, target_count:results.length,
    policy:{
      public_only:true,
      no_api_product_extraction:true,
      no_plugin_discovery_in_execution:true,
      no_sitemap_or_robots_discovery_in_execution:true,
      no_playwright_in_execution:true,
      no_captcha_bypass:true,
      no_clearance_cookie_replay:true,
      no_authentication_bypass:true,
      no_proxy_evasion:true,
      no_random_token_enumeration:true,
      native_acceptance:"current_same_host_google_merchant_xml_payload"
    },
    results
  };
  await writeFile(path.join(outDir, "shard-" + shard + ".json"), JSON.stringify(payload, null, 2) + "\n", "utf8");
  console.log(JSON.stringify({
    shard, sites:results.length,
    native_hits:results.filter(x => x.candidate_hits.length).length,
    verified_urls:results.flatMap(x => x.candidate_hits.map(h => h.final_url)),
    transport_limited:results.filter(x => x.status.includes("TRANSPORT_LIMITED")).length
  }, null, 2));
}

await main();
