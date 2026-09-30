#!/usr/bin/env node
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { gunzipSync } from "node:zlib";
import path from "node:path";
import { setTimeout as delay } from "node:timers/promises";

const FAMILY_PATTERNS = {
  woocommerce_google_product_feed: [
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    ...[100,250,500,1000,2500,5000].map(n => `/?woocommerce_gpf=google&gpf_start=0&gpf_limit=${n}`),
    ...[100,250,1000,5000].map(n => `/woocommerce_gpf/google?gpf_start=0&gpf_limit=${n}`)
  ],
  ctx_feed_webappick: [
    "/?woo_feed=google&wt=xml","/?woo_feed=google-shopping&wt=xml","/?woo_feed=google_shopping&wt=xml",
    "/?woo_feed=google-products&wt=xml","/?woo_feed=google_product_feed&wt=xml",
    "/?woo_feed=google-feed&wt=xml","/?woo_feed=google_feed&wt=xml",
    "/?woo_feed=google-merchant&wt=xml","/?woo_feed=google_merchant&wt=xml",
    "/?woo_feed=gmc&wt=xml","/?woo_feed=googlebase&wt=xml","/?woo_feed=product-feed&wt=xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/feed.xml",
    "/wp-content/uploads/woo-feed/google.xml"
  ],
  adtribes_product_feed_pro: [
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml.gz"
  ],
  wpfm_product_feed_manager: [
    "/wp-content/uploads/wppfm-feeds/Google.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Products.xml",
    "/wp-content/uploads/wppfm-feeds/Google_Product.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Feed.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Products-Feed.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Shopping.xml",
    "/wp-content/uploads/wppfm-feeds/Google-Shopping-Feed.xml",
    "/wp-content/uploads/wppfm-feeds/googlefeed.xml",
    "/wp-content/uploads/wppfm-feeds/google-feed.xml",
    "/wp-content/uploads/wppfm-feeds/google-products-feed.xml",
    "/wp-content/uploads/wppfm-feeds/feed-google.xml",
    "/wp-content/uploads/wppfm-feeds/feed-google-shopping.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping-feed.xml",
    "/wp-content/uploads/wppfm-feeds/feed.xml"
  ],
  webtoffee_product_feed: [
    "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_gs_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml",
    "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_feed.xml",
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
    "/wp-content/uploads/rex-feed/google.xml",
    "/wp-content/uploads/rex-feed/google-feed.xml",
    "/wp-content/uploads/rex-feed/google-product-feed.xml",
    "/wp-content/uploads/rex-feed/google-shopping.xml"
  ]
};

const GENERIC = [
  "/google.xml","/google-feed.xml","/google-products.xml","/google-product-feed.xml",
  "/google-shopping.xml","/google-shopping-feed.xml","/google-merchant.xml",
  "/google-merchant-feed.xml","/merchant.xml","/merchant-feed.xml",
  "/product-feed.xml","/products-feed.xml","/feed.xml","/gpf.xml"
];

const GENERIC_BY_DIR = [
  ["/wp-content/uploads/woo-feed/google/xml/",["google.xml","google-shopping.xml","google-shopping-feed.xml","feed.xml"]],
  ["/wp-content/uploads/woo-product-feed-pro/xml/",["google.xml","google-shopping.xml","google-shopping-feed.xml","feed.xml"]],
  ["/wp-content/uploads/wppfm-feeds/",["google.xml","google-feed.xml","google-products.xml","google-shopping.xml","feed.xml"]],
  ["/wp-content/uploads/webtoffee_product_feed/",["google.xml","google-feed.xml","wt_google_Feed.xml","wt_gs_Feed.xml"]],
  ["/wp-content/uploads/codesolz-feeds/",["google-products.xml","google.xml","google-shopping.xml"]],
  ["/wp-content/uploads/rex-feed/",["feed-1.xml","feed-687.xml","google.xml","google-feed.xml"]]
];

const CHALLENGE_MARKERS = [
  "just a moment","cf-chl-","cf-turnstile","cf-browser-verification",
  "challenge-platform","captcha","access denied","attention required",
  "checking your browser","request blocked"
];

const UA = "Mozilla/5.0 (compatible; WooCommercePluginFamilyGuess/4.0; +https://github.com/Z-Solo-King/foundation)";
const MAX_BODY = 12 * 1024 * 1024;

function sameHost(a,b) {
  try {
    const ah = new URL(a).hostname.toLowerCase().replace(/^www\./,"");
    const bh = new URL(b).hostname.toLowerCase().replace(/^www\./,"");
    return ah === bh;
  } catch { return false; }
}

function canonicalize(root, raw) {
  const u = new URL(raw, root);
  if (!/^https?:$/.test(u.protocol)) throw new Error("non-http");
  u.hash = "";
  if (!sameHost(u.href, root)) throw new Error("cross-host");
  return u.href;
}

function strictValidate(body) {
  if (!body) return {valid:false, reason:"empty"};
  const text = String(body);
  const low = text.toLowerCase();
  if (CHALLENGE_MARKERS.some(m => low.slice(0,30000).includes(m))) {
    return {valid:false, reason:"challenge_or_access_denied"};
  }
  if (/^\s*<(?:urlset|sitemapindex)\b/i.test(text)) return {valid:false, reason:"sitemap"};
  if (!/^\s*(?:<\?xml\b|<rss\b|<feed\b|<channel\b)/i.test(text)) return {valid:false, reason:"not_xml"};
  if (!/https?:\/\/base\.google\.com\/ns\/1\.0/i.test(text)) return {valid:false, reason:"no_google_namespace"};
  const blocks = [
    ...text.matchAll(/<item\b[^>]*>([\s\S]*?)<\/item>/gi),
    ...text.matchAll(/<entry\b[^>]*>([\s\S]*?)<\/entry>/gi)
  ].map(m => m[1]);
  if (!blocks.length) return {valid:false, reason:"no_item_or_entry"};
  let validItems = 0;
  for (const block of blocks) {
    if (["id","title","link","price"].every(f => new RegExp(`<g:${f}\\b[^>]*>[\\s\\S]*?<\\/g:${f}>`,"i").test(block))) {
      validItems++;
    }
  }
  return validItems
    ? {valid:true, reason:"validated_google_merchant_xml", items:blocks.length, valid_items:validItems}
    : {valid:false, reason:"no_item_with_core_google_fields", items:blocks.length, valid_items:0};
}

function identityTokens(site) {
  const host = new URL(site.root).hostname.replace(/^www\./i,"").split(".")[0];
  return [...new Set([host, site.site]
    .flatMap(v => String(v).toLowerCase().split(/[^a-z0-9]+/).filter(Boolean))
    .filter(v => v.length >= 3 && v.length <= 28))]
    .slice(0,6);
}

function addCandidate(map, root, raw, rank, source, family) {
  try {
    const url = canonicalize(root, raw);
    const existing = map.get(url);
    if (!existing || rank > existing.rank) map.set(url,{url,rank,source,family});
  } catch {}
}

function candidatesFor(site) {
  const family = site.family;
  const map = new Map();
  const add = (raw,rank,source,fam=family) => addCandidate(map,site.root,raw,rank,source,fam);

  if (family === "google_for_woocommerce") return {candidates:[],reason:"api_integrated_family"};

  if (family !== "unknown_woocommerce" && FAMILY_PATTERNS[family]) {
    for (const raw of FAMILY_PATTERNS[family]) add(raw,220,"documented-family");
    if (family === "ctx_feed_webappick") {
      for (const n of ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_feed","google-merchant","google_merchant","gmc","googlebase","product-feed","products"])
        add(`/?woo_feed=${n}&wt=xml`,205,"ctx-semantic-query");
    }
    if (family === "webtoffee_product_feed") {
      for (const n of ["wt_google_Feed.xml","wt_gs_Feed.xml","wt_google_feed.xml","wt_google_shopping_Feed.xml","wt_google_shopping_feed.xml","google.xml","google-shopping.xml","google-product-feed.xml","google-shopping-feed.xml"])
        add("/wp-content/uploads/webtoffee_product_feed/"+n,205,"webtoffee-semantic-name");
    }
    for (const [dir,names] of GENERIC_BY_DIR) {
      if ((family === "ctx_feed_webappick" && dir.includes("woo-feed")) ||
          (family === "adtribes_product_feed_pro" && dir.includes("woo-product-feed-pro")) ||
          (family === "wpfm_product_feed_manager" && dir.includes("wppfm-feeds")) ||
          (family === "webtoffee_product_feed" && dir.includes("webtoffee_product_feed")) ||
          (family === "codesolz_merchant_feed_booster" && dir.includes("codesolz-feeds")) ||
          (family === "rexfed_product_feed" && dir.includes("rex-feed"))) {
        for (const n of names) add(dir+n,160,"family-directory-semantic");
      }
    }
    if (family === "wpfm_product_feed_manager" || family === "webtoffee_product_feed" || family === "adtribes_product_feed_pro" || family === "rexfed_product_feed") {
      for (const token of identityTokens(site)) {
        for (const n of ["google.xml","google-feed.xml","google-products.xml","google-product-feed.xml","google-shopping.xml"]) {
          const dir =
            family === "wpfm_product_feed_manager" ? "/wp-content/uploads/wppfm-feeds/" :
            family === "webtoffee_product_feed" ? "/wp-content/uploads/webtoffee_product_feed/" :
            family === "adtribes_product_feed_pro" ? "/wp-content/uploads/woo-product-feed-pro/xml/" :
            "/wp-content/uploads/rex-feed/";
          const base=n.replace(/\.xml$/,"");
          add(dir+token+"-"+base+".xml",125,"bounded-identity-name");
        }
      }
    }
    return {candidates:[...map.values()].sort((a,b)=>b.rank-a.rank || a.url.localeCompare(b.url)).slice(0,160)};
  }

  // Unknown family: a bounded cross-family guess. This is guessing-only; no discovery channels.
  for (const [fam,patterns] of Object.entries(FAMILY_PATTERNS)) {
    for (const raw of patterns) add(raw,190,fam === "rexfed_product_feed" ? "second-wave-documented-family" : "cross-family-documented",fam);
  }
  for (const [dir,names] of GENERIC_BY_DIR) for (const n of names) add(dir+n,120,"cross-family-semantic",dir);
  for (const raw of GENERIC) add(raw,105,"root-generic");
  for (const n of ["google","google-shopping","google_shopping","google-products","google_product_feed","google-feed","google_merchant","gmc","googlebase"]) {
    add(`/?woo_feed=${n}&wt=xml`,110,"cross-family-ctx-query","ctx_feed_webappick");
    add(`/?woocommerce_gpf=${n}`,100,"cross-family-gpf-query","woocommerce_google_product_feed");
  }
  return {candidates:[...map.values()]
    .sort((a,b)=>b.rank-a.rank || a.url.localeCompare(b.url))
    .slice(0,60)};
}

async function fetchCandidate(url, timeoutMs, attempts) {
  let last = {status:0,final_url:url,transport:"request_error",challenge:false,validation:{valid:false,reason:"request_error"}};
  for (let attempt=1; attempt<=attempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const r = await fetch(url,{redirect:"follow",headers:{
        "user-agent":UA,
        "accept":"application/xml,text/xml,application/rss+xml;q=0.9,*/*;q=0.1",
        "cache-control":"no-cache"
      },signal:controller.signal});
      const ab = Buffer.from(await r.arrayBuffer());
      let data = ab;
      if (ab.length>=2 && ab[0]===0x1f && ab[1]===0x8b) {
        try { data=gunzipSync(ab); }
        catch { return {...last,status:r.status,transport:"invalid_gzip"}; }
      }
      const body=data.toString("utf8").slice(0,MAX_BODY);
      const finalUrl=r.url || url;
      const challenge=CHALLENGE_MARKERS.some(m=>body.slice(0,30000).toLowerCase().includes(m));
      const validation=(r.status===200 && sameHost(finalUrl,url)) ? strictValidate(body) : {valid:false,reason:"http_or_redirect"};
      last={status:r.status,final_url:finalUrl,transport:r.ok?"public_http":"http_error",challenge,validation};
      if (validation.valid) return last;
      if (![429,502,503,504].includes(r.status)) return last;
      const retryAfter=Number.parseInt(r.headers.get("retry-after")||"",10);
      await delay(Number.isFinite(retryAfter) ? Math.min(retryAfter*1000,5000) : attempt*900);
    } catch (e) {
      last={status:0,final_url:url,transport:e?.name==="AbortError"?"timeout":"request_error",challenge:false,validation:{valid:false,reason:e?.name==="AbortError"?"timeout":"request_error"}};
      await delay(attempt*500);
    } finally { clearTimeout(timer); }
  }
  return last;
}

async function mapPool(items, concurrency, fn) {
  const out = new Array(items.length);
  let next = 0;
  async function worker() {
    while (true) {
      const i=next++;
      if (i>=items.length) return;
      out[i]=await fn(items[i],i);
    }
  }
  await Promise.all(Array.from({length:Math.max(1,concurrency)},worker));
  return out;
}

async function runOne(site, cfg) {
  const generated=candidatesFor(site);
  if (generated.reason === "api_integrated_family") {
    return {
      site:site.site,root:site.root,family:site.family,evidence:site.evidence,
      guessing_mode:"skipped_api_integrated_family",candidate_count:0,candidate_hits:[],
      status:"API_INTEGRATED_NO_XML_GUESS",transport_summary:{}
    };
  }
  const candidates=generated.candidates;
  const results=await mapPool(candidates,cfg.candidateConcurrency,async c=>{
    const r=await fetchCandidate(c.url,cfg.timeoutMs,cfg.attempts);
    return {...c,...r};
  });
  const hits=results.filter(x=>x.validation.valid && sameHost(x.final_url,site.root));
  return {
    site:site.site,root:site.root,family:site.family,evidence:site.evidence,
    guessing_mode:site.family==="unknown_woocommerce"?"bounded_cross_family":"family_specific",
    candidate_count:candidates.length,candidate_hits:hits.slice(0,5),
    status:hits.length?"NATIVE_FEED_VERIFIED":(
      results.some(x=>x.status===403 || x.status===429 || x.transport==="timeout" || x.challenge)
        ?"NO_NATIVE_FEED_VERIFIED_TRANSPORT_LIMITED":"NO_NATIVE_FEED_VERIFIED"
    ),
    transport_summary:{
      http_200:results.filter(x=>x.status===200).length,
      http_403:results.filter(x=>x.status===403).length,
      http_404:results.filter(x=>x.status===404).length,
      http_429:results.filter(x=>x.status===429).length,
      timeouts:results.filter(x=>x.transport==="timeout").length,
      challenges:results.filter(x=>x.challenge).length
    },
    top_misses:results
      .filter(x=>x.status===200 || x.status===403 || x.status===429 || x.transport==="timeout")
      .slice(0,20)
      .map(x=>({family:x.family,url:x.url,status:x.status,reason:x.validation.reason,final_url:x.final_url}))
  };
}

async function main() {
  const args=process.argv.slice(2);
  const getArg=k=>args.includes(k)?args[args.indexOf(k)+1]:undefined;
  const input=getArg("--input")||"docs/feed-lab/WOOCOMMERCE_PLUGIN_FAMILY_GUESS_MANIFEST_2026-09-30.json";
  const outDir=getArg("--out")||"out/woocommerce-plugin-family-guess-v4";
  const shard=Number(getArg("--shard")||process.env.SHARD||1);
  const shards=Number(getArg("--shards")||process.env.SHARDS||6);
  const siteConcurrency=Math.max(1,Number(getArg("--site-concurrency")||process.env.SITE_CONCURRENCY||1));
  const candidateConcurrency=Math.max(1,Number(getArg("--candidate-concurrency")||process.env.CANDIDATE_CONCURRENCY||6));
  const timeoutMs=Math.max(1500,Number(getArg("--timeout-ms")||process.env.REQUEST_TIMEOUT_MS||6500));
  const attempts=Math.max(1,Number(getArg("--attempts")||process.env.ATTEMPTS||2));
  const matrix=JSON.parse(await readFile(input,"utf8"));
  const selected=matrix.sites.filter((_,i)=>i%shards+1===shard);
  await mkdir(outDir,{recursive:true});
  const results=await mapPool(selected,siteConcurrency,site=>runOne(site,{candidateConcurrency,timeoutMs,attempts}));
  const payload={
    schema:"woocommerce-plugin-family-guess-v4/v1",
    strategy:"plugin-family-specific-xml-guess-only",
    shard,shards,target_count:results.length,
    policy:{
      public_only:true,
      no_api_product_extraction:true,
      no_plugin_discovery_in_execution:true,
      no_captcha_bypass:true,
      no_clearance_cookie_replay:true,
      no_authentication_bypass:true,
      no_proxy_evasion:true,
      no_random_token_enumeration:true,
      native_acceptance:"current_same_host_google_merchant_xml_payload"
    },
    results
  };
  await writeFile(path.join(outDir,`shard-${shard}.json`),JSON.stringify(payload,null,2)+"\n","utf8");
  console.log(JSON.stringify({
    shard,sites:results.length,
    native_hits:results.filter(x=>x.candidate_hits.length).length,
    verified_urls:results.flatMap(x=>x.candidate_hits.map(h=>h.final_url)),
    transport_limited:results.filter(x=>x.status.includes("TRANSPORT_LIMITED")).length
  },null,2));
}
await main();
