#!/usr/bin/env node
import { mkdir, writeFile } from "node:fs/promises";

export const TARGETS = [
  ["Aarna Computers","https://aarnacomputers.com"],
  ["Ads Store","https://adsstore.in"],
  ["avikaretails","https://avikaretails.com"],
  ["EZPZ Solutions","https://www.ezpzsolutions.in"],
  ["GamesNComps","https://gamesncomps.com"],
  ["Geekbees","https://geekbees.in"],
  ["hotshiftpc","https://hotshiftpc.com"],
  ["itgadgetsonline","https://itgadgetsonline.com"],
  ["ithunt","https://ithunt.in"],
  ["KC Computers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["Kryptronix Gaming","https://kryptronix.in"],
  ["NCL Computer","https://nclcomputer.com"],
  ["networkitstore","https://networkitstore.in"],
  ["nexusinfosys","https://www.mynexusinfosys.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PC Studio","https://www.pcstudio.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["Prime ABGB","https://www.primeabgb.com"],
  ["quickincomputers","https://quickincomputers.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["solankienterprises","https://solankienterprises.com"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Viper PC","https://viperpc.in"],
  ["AULA India","https://aulaindia.com"],
  ["Cosmic Byte","https://www.thecosmicbyte.com"],
  ["Meckeys","https://www.meckeys.com"],
  ["Moskeys","https://moskeys.com"],
  ["Ninja Dog","https://ninjadog.in"],
  ["StacksKB","https://stackskb.com"],
  ["Theproaudio","https://www.theproaudio.com"],
];

const FEED_FAMILIES = {
  woocommerce_google_product_feed: {
    markers: ["woocommerce-google-product-feed","woocommerce_gpf","woocommerce_gpf_google"],
    pluginSlugs: ["woocommerce-google-product-feed"],
  },
  ctx_feed_webappick: {
    markers: ["webappick","ctx-feed","ctxfeed","woo-feed","woo_feed="],
    pluginSlugs: ["woo-feed"],
  },
  adtribes_product_feed_pro: {
    markers: ["woo-product-feed-pro","adtribes","woosea"],
    pluginSlugs: ["woo-product-feed-pro"],
  },
  webtoffee_product_feed: {
    markers: ["webtoffee","webtoffee_product_feed"],
    pluginSlugs: ["webtoffee"],
  },
  wpfm_product_feed_manager: {
    markers: ["wppfm","product feed manager","woocommerce product feed manager"],
    pluginSlugs: ["wppfm"],
  },
  codesolz_feed: {
    markers: ["codesolz","codesolz-feeds"],
    pluginSlugs: ["merchant-feed-booster-lite-for-woocommerce"],
  },
  feedcraft: {
    markers: ["feedcraft-product-feed","feedcraft product feed"],
    pluginSlugs: ["thebasics-product-feed"],
  },
  google_for_woocommerce: {
    markers: ["google-listings-and-ads","google for woocommerce","google-merchant-api","google merchant api"],
    pluginSlugs: ["google-listings-and-ads"],
  },
};

const ENDPOINTS = [
  {name:"homepage", path:"/"},
  {name:"wp-json", path:"/wp-json/"},
  {name:"rest-route-root", path:"/?rest_route=/"},
  {name:"wp-v2", path:"/wp-json/wp/v2/"},
  {name:"rest-route-wp-v2", path:"/?rest_route=/wp/v2/"},
  {name:"robots", path:"/robots.txt"},
  {name:"sitemap-index", path:"/sitemap_index.xml"},
  {name:"wp-sitemap", path:"/wp-sitemap.xml"},
  {name:"readme", path:"/readme.html"},
  {name:"license", path:"/license.txt"},
];

const CHALLENGE_MARKERS = [
  "just a moment","cf-chl-","cf-turnstile","turnstile","captcha",
  "access denied","attention required","checking your browser"
];

const UA = "Mozilla/5.0 (compatible; WooCommercePluginResearch/2.0; +https://github.com/Z-Solo-King/foundation)";
const ACCEPT = "text/html,application/json,text/plain;q=0.9,*/*;q=0.1";

const sleep = (ms) => new Promise(r => setTimeout(r, ms));

function originVariants(root) {
  const u = new URL(root);
  const host = u.hostname;
  const variants = [root.replace(/\/+$/, "")];
  if (host.startsWith("www.")) variants.push(new URL(u.toString().replace(/^https?:\/\//,"https://").replace("www.",""), u.toString()).origin);
  else variants.push("https://www." + host);
  if (u.protocol === "https:") variants.push("http://" + host);
  return [...new Set(variants.filter(Boolean))];
}

async function fetchPublic(url, timeoutMs = 7000, attempts = 3) {
  let last = {status:0,url,body:"",contentType:"",headers:{},transport:"request_error"};
  for (let attempt=1; attempt<=attempts; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const r = await fetch(url, {
        headers: { "user-agent": UA, "accept": ACCEPT },
        redirect: "follow",
        signal: controller.signal,
      });
      const body = (await r.text()).slice(0, 8*1024*1024);
      const headers = {
        "content-type": r.headers.get("content-type") || "",
        "server": r.headers.get("server") || "",
        "x-powered-by": r.headers.get("x-powered-by") || "",
        "retry-after": r.headers.get("retry-after") || "",
      };
      last = {
        status:r.status, url:r.url || url, body, contentType:headers["content-type"],
        headers, transport:r.ok ? "public_http" : "http_error",
        challenge: CHALLENGE_MARKERS.some(x => body.slice(0,20000).toLowerCase().includes(x))
      };
      if (![429,502,503,504].includes(r.status)) return last;
      const retryAfter = Number.parseInt(headers["retry-after"], 10);
      await sleep(Number.isFinite(retryAfter) ? Math.min(retryAfter*1000,5000) : attempt*750);
    } catch (error) {
      last = {
        status:0, url, body:"", contentType:"", headers:{},
        transport:error?.name==="AbortError" ? "timeout" : "request_error",
        error:String(error?.message || error)
      };
      await sleep(attempt*500);
    } finally { clearTimeout(timer); }
  }
  return last;
}

function snippet(source, marker) {
  const s=String(source||""); const i=s.toLowerCase().indexOf(marker.toLowerCase());
  if(i<0) return "";
  return s.slice(Math.max(0,i-100), Math.min(s.length,i+220)).replace(/\s+/g," ").trim();
}

function extractJsonNamespaces(text) {
  try {
    const data = JSON.parse(text);
    const values = [];
    if (Array.isArray(data?.namespaces)) values.push(...data.namespaces);
    for (const key of Object.keys(data || {})) if (/woo|feed|google|merchant|product/i.test(key)) values.push(key);
    return [...new Set(values.map(String))].slice(0,100);
  } catch { return []; }
}

function extractPluginAssets(text) {
  const assets = new Map();
  const source = String(text||"");
  const re = /\/wp-content\/plugins\/([^/?"'\\#]+)(?:\/[^?"'\\#\s<]*)?(?:[?&]ver=([^"'&\s<]+))?/gi;
  for (const m of source.matchAll(re)) {
    const slug = decodeURIComponent(m[1]).toLowerCase();
    if (!assets.has(slug)) assets.set(slug, new Set());
    if (m[2]) assets.get(slug).add(m[2]);
  }
  return [...assets.entries()].map(([slug,versions]) => ({slug, versions:[...versions]}));
}

function feedSignals(source, namespaces=[]) {
  const lower = String(source||"").toLowerCase();
  const ns = namespaces.map(x=>String(x).toLowerCase());
  const found = [];
  for (const [family,spec] of Object.entries(FEED_FAMILIES)) {
    const matches = [];
    for (const marker of spec.markers) {
      if (lower.includes(marker.toLowerCase())) matches.push({marker,snippet:snippet(source,marker)});
    }
    if (matches.length) found.push({family, confidence:matches.length>=2?"strong":"signal", matches});
  }
  const namespaceFamilies = new Map([
    ["wpfm/v1", "wpfm_product_feed_manager"],
    ["wppfm/v1", "wpfm_product_feed_manager"],
  ]);
  for (const [marker, family] of namespaceFamilies) {
    if (ns.some(x=>x===marker || x.startsWith(marker+"/"))) {
      const existing=found.find(x=>x.family===family);
      const entry={marker:`namespace:${marker}`, snippet:`WP-JSON namespace ${marker}`};
      if (existing) {
        existing.matches.push(entry);
        existing.confidence="strong";
      } else {
        found.push({family, confidence:"strong", matches:[entry]});
      }
    }
  }
  return found;
}

function feedLikeAssets(assets) {
  const allow = /(?:^|[-_])(?:feed|product-feed|google-product-feed|merchant-feed|shopping-feed)(?:$|[-_])|^(?:woo-feed|woo-product-feed-pro|best-woocommerce-feed|webappick-product-feed-for-woocommerce|merchant-feed-booster-lite-for-woocommerce|thebasics-product-feed|product-feed-manager|product-feed-for-woocommerce|rex-product-feed|conversios)$/i;
  return assets.map(x=>x.slug).filter(slug =>
    allow.test(slug) &&
    !/^(?:instagram-feed|advanced-ads|feedzy-rss-feeds|facebook-for-woocommerce)$/i.test(slug)
  ).slice(0,50);
}

function choosePrimary(families, assets) {
  const priority = [
    "woocommerce_google_product_feed","ctx_feed_webappick","adtribes_product_feed_pro",
    "webtoffee_product_feed","wpfm_product_feed_manager","codesolz_feed","feedcraft","google_for_woocommerce"
  ];
  for (const family of priority) if (families.some(x=>x.family===family)) return family;
  const knownAssetFamilies = new Map([
    ["woo-feed","ctx_feed_webappick"],
    ["webappick-product-feed-for-woocommerce","ctx_feed_webappick"],
    ["ctx-feed","ctx_feed_webappick"],
    ["woo-product-feed-pro","adtribes_product_feed_pro"],
    ["merchant-feed-booster-lite-for-woocommerce","codesolz_feed"],
    ["thebasics-product-feed","feedcraft"],
    ["product-feed-manager","wpfm_product_feed_manager"],
    ["wppfm","wpfm_product_feed_manager"],
  ]);
  for (const asset of assets) {
    const family = knownAssetFamilies.get(asset.slug);
    if (family) return family;
  }
  return "unknown_woocommerce";
}

function generatorTags(source) {
  const out=[];
  for (const re of [
    /<meta[^>]+name=["']generator["'][^>]+content=["']([^"']+)["']/gi,
    /<meta[^>]+content=["']([^"']+)["'][^>]+name=["']generator["']/gi
  ]) for (const m of String(source||"").matchAll(re)) out.push(m[1].trim());
  return [...new Set(out)];
}

function identityTokens(source, root) {
  const toks = [];
  try { toks.push(new URL(root).hostname.replace(/^www\./i,"").split(".")[0]); } catch {}
  for (const re of [
    /<meta[^>]+property=["']og:site_name["'][^>]+content=["']([^"']+)["']/gi,
    /<meta[^>]+content=["']([^"']+)["'][^>]+property=["']og:site_name["']/gi,
    /<title[^>]*>([^<]{2,160})<\/title>/gi,
  ]) for (const m of String(source||"").matchAll(re)) toks.push(m[1]);
  return [...new Set(toks.flatMap(x=>String(x).toLowerCase().split(/[^a-z0-9]+/).filter(x=>x.length>=2&&x.length<=32)))].slice(0,20);
}

async function inspect(name, root) {
  const variants = originVariants(root);
  let endpointResults = [];
  let homeBody = "";
  let apiBody = "";
  let selectedOrigin = root;

  for (const origin of variants) {
    const batch = await Promise.all(
      ENDPOINTS.map(ep => fetchPublic(origin + ep.path))
    );
    endpointResults.push(...batch.map((r,i)=>({
      origin,
      endpoint:ENDPOINTS[i].name,
      status:r.status,
      finalUrl:r.url,
      contentType:r.contentType,
      transport:r.transport,
      challenge:!!r.challenge,
      bytes:r.body.length,
      server:r.headers?.server || "",
      xPoweredBy:r.headers?.["x-powered-by"] || ""
    })));

    const home = batch[0];
    if (home.status===200 && home.body) {
      homeBody=home.body;
      try { selectedOrigin=new URL(home.url).origin; } catch {}
      apiBody = batch
        .filter((r,i)=>["wp-json","rest-route-root","wp-v2","rest-route-wp-v2"].includes(ENDPOINTS[i].name) && r.status===200)
        .map(r=>r.body).join("\n");
      break;
    }
  }

  const combined = homeBody + "\n" + apiBody;
  const assets = extractPluginAssets(combined);
  const namespaces = extractJsonNamespaces(apiBody);
  const families = feedSignals(combined, namespaces);
  const feedAssets = feedLikeAssets(assets);
  const readmeTargets = [...new Set([
    ...feedAssets,
    ...families.flatMap(x=>FEED_FAMILIES[x.family]?.pluginSlugs || [])
  ])].slice(0,8);

  const readmes = (await Promise.all(readmeTargets.map(async slug => {
    for (const file of ["readme.txt","README.md"]) {
      const r=await fetchPublic(selectedOrigin+"/wp-content/plugins/"+encodeURIComponent(slug)+"/"+file,4000,2);
      if (r.status===200 && r.body && !r.challenge) {
        const title=(r.body.match(/^===\s*(.+?)\s*===/m)||[])[1] || "";
        const version=(r.body.match(/^Stable tag:\s*(.+)$/im)||[])[1] || "";
        const nameLine=(r.body.match(/^Plugin Name:\s*(.+)$/im)||[])[1] || title;
        return {slug,file,pluginName:nameLine.trim(),stableTag:version.trim(),bytes:r.body.length};
      }
    }
    return null;
  }))).filter(Boolean);

  const feedFamily = choosePrimary(families,assets);
  const status = homeBody
    ? (families.length || feedAssets.length ? "PLUGIN_SIGNALS_FOUND" : "WOOCOMMERCE_PLUGIN_SURFACE_NO_FEED_SIGNAL")
    : (endpointResults.some(x=>x.challenge) ? "PUBLIC_CHALLENGE_NO_PLUGIN_SURFACE" : "PUBLIC_FETCH_UNAVAILABLE");

  return {
    schema_version:"woocommerce-31-plugin-extraction/v3",
    site:name, configured_root:root, selected_origin:selectedOrigin,
    status,
    platform:"woocommerce_corpus",
    endpoints:endpointResults,
    plugin_assets:assets,
    feed_like_plugin_assets:feedAssets,
    feed_family_signals:families,
    primary_group:feedFamily,
    readme_metadata:readmes,
    wordpress_generator:generatorTags(combined),
    identity_tokens:identityTokens(homeBody,root),
    public_api_namespaces:namespaces,
  };
}

async function main() {
  const args=process.argv.slice(2); const get=k=>{const i=args.indexOf(k); return i>=0?args[i+1]:null;};
  const name=get("--site"), root=get("--root"), out=get("--out");
  if(!name || !root || !out) throw new Error("usage: --site <name> --root <url> --out <path>");
  await mkdir(out.split("/").slice(0,-1).join("/")||".",{recursive:true});
  const report=await inspect(name,root);
  await writeFile(out,JSON.stringify(report,null,2)+"\n");
  console.log(JSON.stringify({site:name,primary_group:report.primary_group,status:report.status,assets:report.plugin_assets.length,feed_like:report.feed_like_plugin_assets},null,2));
}

if (process.argv[1] && process.argv[1].endsWith("woocommerce_31_plugin_extract.mjs")) await main();
