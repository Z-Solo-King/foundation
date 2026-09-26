import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";

const targets = [
  ["Aarna Computers","https://aarnacomputers.com"],
  ["Ads Store","https://adsstore.in"],
  ["avikaretails","https://avikaretails.com"],
  ["EZPZ Solutions","https://www.ezpzsolutions.in"],
  ["GamesNComps","https://gamesncomps.com"],
  ["Geekbees","https://geekbees.in"],
  ["hotshiftpc","https://hotshiftpc.com"],
  ["itgadgetsonline","https://itgadgetsonline.com"],
  ["ithunt","https://ithunt.in"],
  ["kccomputers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["Kryptronix Gaming","https://kryptronix.in"],
  ["NCL Computer","https://nclcomputer.com"],
  ["networkitstore","https://networkitstore.in"],
  ["nexusinfosys","https://www.mynexusinfosys.com"],
  ["Only SDD","https://onlyssd.com"],
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
  ["Theproaudio","https://www.theproaudio.com"]
];

const DETERMINISTIC = [
  "/?woocommerce_gpf=google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
  "/woocommerce_gpf/google",
  "/?woocommerce_gpf=googleinventory",
  "/?feed=google",
  "/?feed=google_shopping",
  "/?feed=google_shopping_feed",
  "/?feed=google-product-feed",
  "/?product_feed=google",
  "/google.xml",
  "/google-products.xml",
  "/google-product-feed.xml",
  "/google-shopping.xml",
  "/google-shopping-feed.xml",
  "/product-feed.xml",
  "/products-feed.xml",
  "/merchant-feed.xml",
  "/google/feed.xml",
  "/feed/google.xml",
  "/feed/google-shopping.xml",
  "/feed/google-products.xml",
  "/feeds/google.xml",
  "/feeds/google-products.xml",
  "/feeds/google-product-feed.xml",
  "/feeds/google-shopping.xml",
  "/wp-content/uploads/google-products.xml",
  "/wp-content/uploads/google-product-feed.xml",
  "/wp-content/uploads/google-shopping.xml",
  "/wp-content/uploads/google-shopping-feed.xml",
  "/wp-content/uploads/feeds/google-products.xml",
  "/wp-content/uploads/feeds/google-product-feed.xml",
  "/wp-content/uploads/feeds/google-shopping.xml",
  "/wp-content/uploads/woo-feed/google/xml/",
  "/wp-content/uploads/woo-feed/google/",
  "/wp-content/uploads/woo-feed/xml/",
  "/wp-content/uploads/woo-product-feed-pro/xml/",
  "/wp-content/uploads/wppfm-feeds/",
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-json/feedcraft-product-feed/v1/xml",
  "/wp-json/feedcraft-product-feed/v1/json"
];

const UA = "Mozilla/5.0 (compatible; WooCommerceGoogleFeedAudit/2.0)";
const TIMEOUT_MS = 12000;
const MAX_BODY = 50 * 1024 * 1024;
const CONCURRENCY = 6;
const start = Math.max(0, Number.parseInt(process.env.TARGET_START || "0", 10) || 0);
const count = Math.max(1, Number.parseInt(process.env.TARGET_COUNT || String(targets.length), 10) || targets.length);
const selected = targets.slice(start, start + count);

await mkdir("out/feeds", { recursive: true });

function absolute(raw, base) {
  try {
    const u = new URL(String(raw || "").trim(), base);
    return /^https?:$/.test(u.protocol) ? u.href : "";
  } catch { return ""; }
}

function slug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80) || "site";
}

function challenge(text, status) {
  const s = String(text || "").slice(0, 20000).toLowerCase();
  return [403, 429, 430, 451, 503, 520, 521, 522, 523, 524].includes(status) &&
    /just a moment|cf-chl|cloudflare|challenge-platform|cf-turnstile|turnstile|captcha|verify you are human|access denied|request blocked|attention required|checking your browser/.test(s);
}

function parseRobots(text, base) {
  const disallow = [];
  const sitemaps = [];
  let wildcard = false;
  for (const raw of String(text || "").split(/\r?\n/)) {
    const line = raw.replace(/#.*$/, "").trim();
    if (!line) continue;
    const [k, ...rest] = line.split(":");
    const v = rest.join(":").trim();
    if (/^user-agent$/i.test(k)) wildcard = v === "*";
    if (wildcard && /^disallow$/i.test(k) && v) disallow.push(v);
    if (/^sitemap$/i.test(k) && v) {
      const u = absolute(v, base); if (u) sitemaps.push(u);
    }
  }
  return { disallow, sitemaps };
}

function robotsBlocked(pathname, robots) {
  for (const rule of robots.disallow || []) {
    if (rule === "/") return true;
    if (rule.endsWith("*") && pathname.startsWith(rule.slice(0, -1))) return true;
    if (rule && !rule.includes("*") && pathname.startsWith(rule)) return true;
  }
  return false;
}

function htmlFeedLinks(text, base) {
  const out = new Set();
  for (const m of String(text || "").matchAll(/<link\b[^>]*>/gi)) {
    const tag = m[0];
    const href = (tag.match(/\bhref=["']([^"']+)["']/i) || [])[1];
    const rel = (tag.match(/\brel=["']([^"']+)["']/i) || [])[1] || "";
    const type = (tag.match(/\btype=["']([^"']+)["']/i) || [])[1] || "";
    if (!href || !/alternate/i.test(rel)) continue;
    if (!/xml|rss|atom/i.test(type) && !/google|merchant|feed|product/i.test(href)) continue;
    const u = absolute(href, base); if (u) out.add(u);
  }
  for (const raw of String(text || "").matchAll(/(?:(?:https?:)?\/\/|\/)[:/?#A-Za-z0-9._%~+\-=&]+/g)) {
    const u = absolute(raw[0], base);
    if (u && /(?:google|merchant|feed|product).*\.xml(?:[?#]|$)/i.test(u)) out.add(u);
  }
  return [...out];
}

function wpRoutes(text, base) {
  const out = new Set();
  try {
    const data = JSON.parse(text);
    for (const route of Object.keys(data?.routes || {})) {
      if (!/feed|google|merchant|product/i.test(route)) continue;
      if (!/xml|json|feed|product/i.test(route)) continue;
      const u = absolute("/wp-json" + route.replace(/^\/+/, "/"), base);
      if (u) out.add(u);
    }
    for (const ns of data?.namespaces || []) {
      if (!/feedcraft|feed|google|merchant/i.test(String(ns))) continue;
      const u = absolute("/wp-json/" + String(ns).replace(/^\/+/, ""), base);
      if (u) out.add(u);
    }
  } catch {}
  return [...out];
}

function googleNamespaceAliases(xml) {
  const aliases = new Set();
  const re = /xmlns(?::([A-Za-z_][\w.-]*))?\s*=\s*["']http:\/\/base\.google\.com\/ns\/1\.0["']/gi;
  for (const m of String(xml || "").matchAll(re)) aliases.add(m[1] || "");
  return aliases;
}

function field(block, aliases, name) {
  for (const alias of aliases) {
    const p = alias ? `<${alias}:${name}\\b[^>]*>([\\s\\S]*?)</${alias}:${name}>` : `<${name}\\b[^>]*>([\\s\\S]*?)</${name}>`;
    const m = block.match(new RegExp(p, "i")); if (m && m[1].trim()) return m[1].replace(/<[^>]+>/g, "").trim();
  }
  return "";
}

function validateGoogleXml(xml, contentType) {
  const text = String(xml || "");
  const rootOk = /^\s*(?:<\?xml[^>]*>\s*)?(?:<rss\b|<feed\b)/i.test(text);
  const aliases = googleNamespaceAliases(text);
  const items = [...text.matchAll(/<(?:item|entry)\b[^>]*>([\s\S]*?)<\/(?:item|entry)>/gi)].map(m => m[1]);
  let complete = 0;
  const rows = [];
  for (const block of items) {
    const row = {
      id: field(block, aliases, "id"),
      title: field(block, aliases, "title"),
      link: field(block, aliases, "link"),
      price: field(block, aliases, "price"),
      availability: field(block, aliases, "availability"),
      brand: field(block, aliases, "brand"),
      gtin: field(block, aliases, "gtin"),
      mpn: field(block, aliases, "mpn"),
      image_link: field(block, aliases, "image_link")
    };
    complete += [row.id,row.title,row.link,row.price].filter(Boolean).length;
    if (Object.values(row).some(Boolean)) rows.push(row);
  }
  const coverage = complete / Math.max(1, items.length * 4);
  const qualifies = rootOk && aliases.size > 0 && items.length > 0 && coverage >= 0.75;
  return {
    qualifies,
    feed_type: /inventory/i.test(text.slice(0, 20000)) ? "google_inventory" : "google_product",
    namespace_aliases: [...aliases],
    item_count: items.length,
    required_field_coverage: Number(coverage.toFixed(4)),
    sample: rows.slice(0, 3),
    content_type: String(contentType || "")
  };
}

async function get(url) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
  try {
    const r = await fetch(url, {
      method: "GET",
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/xml, text/xml, application/json, text/html;q=0.9, */*"
      }
    });
    const buf = Buffer.from(await r.arrayBuffer());
    return {
      status: r.status,
      finalUrl: r.url,
      contentType: r.headers.get("content-type") || "",
      bytes: buf.length,
      text: buf.length <= MAX_BODY ? buf.toString("utf8") : "",
      buffer: buf.length <= MAX_BODY ? buf : null
    };
  } finally { clearTimeout(timer); }
}

async function scan([name, base]) {
  const candidates = new Map();
  const evidence = [];
  let home = null, robots = {disallow:[],sitemaps:[]}, wp = null;

  for (const path of ["/", "/robots.txt", "/wp-json/"]) {
    try {
      const r = await get(base + path);
      if (path === "/") home = r;
      else if (path === "/robots.txt") robots = parseRobots(r.text, r.finalUrl || base);
      else wp = r;
      evidence.push({kind:path === "/" ? "homepage" : path === "/robots.txt" ? "robots" : "wp_rest", status:r.status, content_type:r.contentType, bytes:r.bytes, final_url:r.finalUrl, challenged:challenge(r.text,r.status)});
    } catch (e) {
      evidence.push({kind:path.slice(1) || "homepage", error:e?.name || String(e)});
    }
  }

  if (home?.text) for (const u of htmlFeedLinks(home.text, home.finalUrl || base)) candidates.set(u, "html_explicit");
  if (wp?.status === 200 && wp.text) for (const u of wpRoutes(wp.text, wp.finalUrl || base)) candidates.set(u, "wp_rest_index");

  for (const s of robots.sitemaps || []) candidates.set(s, "robots_sitemap");

  const dirs = DETERMINISTIC.filter(p => p.endsWith("/"));
  for (const path of DETERMINISTIC) {
    const u = new URL(path, base + "/").href;
    if (!robotsBlocked(new URL(u).pathname, robots)) candidates.set(u, "woocommerce_deterministic");
    else evidence.push({url:u,source:"woocommerce_deterministic",status:null,classification:"ROBOTS_DISALLOWED"});
  }

  // Publicly disclosed XML names in deterministic feed directories, when listings exist.
  for (const dir of dirs) {
    const u = new URL(dir, base + "/").href;
    if (robotsBlocked(new URL(u).pathname, robots)) continue;
    try {
      const r = await get(u);
      if (r.status === 200 && r.text) {
        for (const m of r.text.matchAll(/href=["']([^"']+\.xml(?:\?[^"']*)?)["']/gi)) {
          const x = absolute(m[1], r.finalUrl);
          if (x && new URL(x).origin === new URL(base).origin) candidates.set(x, "public_feed_directory");
        }
      }
      evidence.push({url:u,source:"public_feed_directory",status:r.status,content_type:r.contentType,bytes:r.bytes,classification:r.status===200?"DIRECTORY_LISTING":r.status===403?"PATH_GUARDED":"NO_MATCH"});
    } catch (e) { evidence.push({url:u,source:"public_feed_directory",classification:"ERROR",error:e?.name || String(e)}); }
  }

  const list=[...candidates.entries()];
  let cursor=0;
  const probes=[];
  const feedFiles=[];
  async function worker() {
    while (cursor < list.length) {
      const [url,source]=list[cursor++];
      let u; try { u = new URL(url); } catch { continue; }
      if (robotsBlocked(u.pathname, robots)) {
        probes.push({url,source,classification:"ROBOTS_DISALLOWED"}); continue;
      }
      try {
        const r = await get(url);
        if (r.status === 200 && r.text) {
          const parsed = validateGoogleXml(r.text, r.contentType);
          if (parsed.qualifies) {
            const hash = createHash("sha256").update(r.buffer || Buffer.from(r.text)).digest("hex");
            const file = `out/feeds/${slug(name)}-${hash.slice(0,12)}.xml`;
            await writeFile(file, r.buffer || Buffer.from(r.text));
            feedFiles.push({url,final_url:r.finalUrl,file,sha256:hash,bytes:r.bytes,...parsed,source});
            probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"LIVE_VERIFIED",...parsed,sha256:hash});
          } else {
            probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"NO_MATCH",...parsed});
          }
        } else if (r.status===401) {
          probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"AUTH_REQUIRED"});
        } else if (challenge(r.text,r.status)) {
          probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"BLOCKED_OR_CHALLENGED"});
        } else if (r.status===403) {
          probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"ACCESS_DENIED"});
        } else if (r.status===429) {
          probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:"RATE_LIMITED"});
        } else {
          probes.push({url,source,status:r.status,final_url:r.finalUrl,bytes:r.bytes,classification:`HTTP_${r.status}`});
        }
      } catch (e) {
        probes.push({url,source,classification:e?.name === "AbortError" ? "TIMEOUT" : "ERROR",error:e?.name || String(e)});
      }
    }
  }
  await Promise.all(Array.from({length:Math.min(CONCURRENCY,list.length||1)},worker));

  const counts = {};
  for (const x of [...evidence,...probes]) counts[x.classification || "INFO"] = (counts[x.classification || "INFO"] || 0) + 1;
  return {
    name, base,
    homepage_status: home?.status ?? null,
    robots: {disallow:robots.disallow,sitemaps:robots.sitemaps},
    candidate_count:list.length,
    feed_count:feedFiles.length,
    feeds:feedFiles,
    counts,
    evidence,
    probes
  };
}

const results=[];
for(let i=0;i<selected.length;i++){
  const r=await scan(selected[i]); results.push(r);
  console.log(JSON.stringify({name:r.name,feed_count:r.feed_count,candidate_count:r.candidate_count,live:r.feeds.map(x=>x.url),counts:r.counts}));
}

const index = {
  schema_version:"woocommerce-google-feed-audit/v4",
  generated_at:new Date().toISOString(),
  target_count:selected.length,
  results,
  feeds:results.flatMap(r=>r.feeds.map(f=>({brand:r.name,base:r.base,...f})))
};
await writeFile("out/woocommerce_google_feed_audit.json", JSON.stringify(index,null,2)+"\n");
await writeFile("out/woocommerce_google_feeds.tsv",
  ["brand","base","url","final_url","feed_type","item_count","required_field_coverage","bytes","sha256","source"]
    .concat(index.feeds.map(f=>[f.brand,f.base,f.url,f.final_url,f.feed_type,f.item_count,f.required_field_coverage,f.bytes,f.sha256,f.source].map(v=>String(v??"").replaceAll("\t"," ")).join("\t")))
    .join("\n")+"\n"
);
await writeFile("out/summary.json", JSON.stringify({
  target_count:selected.length,
  live_verified_feeds:index.feeds.length,
  live_verified_sites:new Set(index.feeds.map(x=>x.brand)).size,
  sites:results.map(r=>({brand:r.name,homepage_status:r.homepage_status,candidate_count:r.candidate_count,feed_count:r.feed_count,feeds:r.feeds.map(x=>x.url),counts:r.counts}))
},null,2)+"\n");
console.log(JSON.stringify({targets:selected.length,live_verified_feeds:index.feeds.length,live_verified_sites:new Set(index.feeds.map(x=>x.brand)).size},null,2));
