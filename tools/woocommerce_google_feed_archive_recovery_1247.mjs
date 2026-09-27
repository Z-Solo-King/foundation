import { mkdir, writeFile, readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { createGunzip } from "node:zlib";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { Readable } from "node:stream";

const execFileAsync = promisify(execFile);

const TARGETS = [
  ["ithunt", "https://ithunt.in"],
  ["kccomputers", "https://kccomputers.co.in"],
  ["KRG KART", "https://krgkart.com"],
  ["PC Kumar Infotech", "https://pckumar.in"],
  ["PCHubShop", "https://www.pchubshop.com"],
  ["SCL Gaming", "https://sclgaming.in"],
  ["Variety Infotech", "https://varietyinfotech.com"],
  ["Moskeys", "https://moskeys.com"],
  ["Theproaudio", "https://www.theproaudio.com"],
];

const OUT = "out/archive-recovery-1247";
const UA = "Mozilla/5.0 (compatible; PickPCPartsFeedResearch/1.0)";
const MAX_BYTES = 50 * 1024 * 1024;
const LIVE_TIMEOUT_MS = 25000;
const ARCHIVE_TIMEOUT_MS = 30000;
const SLEEP_MS = 1800;

const KNOWN_PATHS = [
  "/?woocommerce_gpf=google",
  "/woocommerce_gpf/google",
  "/google.xml",
  "/google-products.xml",
  "/google-product-feed.xml",
  "/google-shopping.xml",
  "/google-shopping-feed.xml",
  "/product-feed.xml",
  "/products-feed.xml",
  "/merchant-feed.xml",
  "/feed/google.xml",
  "/feed/google-products.xml",
  "/feeds/google.xml",
  "/feeds/google-products.xml",
  "/feeds/google-product-feed.xml",
  "/feeds/google-shopping.xml",
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
  "/google-merchant.xml",
  "/google-merchant-feed.xml",
];

function sleep(ms) {
  return new Promise(r => setTimeout(r, ms));
}

function slug(s) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 80) || "site";
}

function canonicalOrigin(base) {
  return new URL(base).origin;
}

function sameOrigin(url, base) {
  try {
    return new URL(url).origin === new URL(base).origin;
  } catch {
    return false;
  }
}

function absoluteUrl(raw, base) {
  try {
    return new URL(raw, base + "/").href;
  } catch {
    return null;
  }
}

function challengeLike(status, text = "") {
  const body = String(text).slice(0, 12000).toLowerCase();
  return (
    [403, 429, 430, 451, 503, 520, 521, 522, 523, 524].includes(Number(status)) &&
    /cloudflare|just a moment|challenge-platform|turnstile|captcha|access denied|request blocked|attention required|checking your browser/.test(body)
  );
}

function looksGoogleMerchantXml(text, contentType = "") {
  const x = String(text || "");
  const head = x.slice(0, 250000);
  if (!/(xml|rss|atom)/i.test(String(contentType || "")) &&
      !/<rss\b/i.test(head) &&
      !/<feed\b/i.test(head)) return false;
  return /xmlns(?::[\w.-]+)?\s*=\s*["']https?:\/\/base\.google\.com\/ns\/1\.0["']/i.test(head)
    && /<(?:[\w.-]+:)?item\b/i.test(x)
    && /<(?:[\w.-]+:)?price\b/i.test(x)
    && /<(?:[\w.-]+:)?title\b/i.test(x);
}

function parseLinks(html, base, includeAll = false) {
  const out = new Set();
  const re = /(?:href|src)\s*=\s*["']([^"']+)["']/gi;
  let m;
  while ((m = re.exec(String(html || "")))) {
    const u = absoluteUrl(m[1], base);
    if (!u || !sameOrigin(u, base)) continue;
    if (includeAll || /google|merchant|shopping|feed|xml|woocommerce_gpf|woo-feed|wppfm|product-feed|feedcraft/i.test(u)) {
      out.add(u);
    }
  }
  return [...out];
}

async function fetchBuffer(url, timeoutMs = LIVE_TIMEOUT_MS, extraHeaders = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      redirect: "follow",
      signal: controller.signal,
      headers: {
        "User-Agent": UA,
        "Accept": "application/xml,application/rss+xml,text/xml,application/json,text/html;q=0.8,*/*;q=0.2",
        ...extraHeaders,
      },
    });
    const buf = Buffer.from(await res.arrayBuffer());
    if (buf.length > MAX_BYTES) {
      return {
        status: res.status,
        url: res.url,
        contentType: res.headers.get("content-type") || "",
        headers: Object.fromEntries(res.headers.entries()),
        buf: null,
        bytes: buf.length,
        error: "response_too_large",
      };
    }
    return {
      status: res.status,
      url: res.url,
      contentType: res.headers.get("content-type") || "",
      headers: Object.fromEntries(res.headers.entries()),
      buf,
      bytes: buf.length,
    };
  } catch (err) {
    return {
      status: 0,
      url,
      contentType: "",
      headers: {},
      buf: null,
      bytes: 0,
      error: err?.name === "AbortError" ? "TIMEOUT" : String(err?.code || err?.name || err),
    };
  } finally {
    clearTimeout(timer);
  }
}

async function curlRaw(url, timeoutMs = LIVE_TIMEOUT_MS) {
  try {
    const args = [
      "-sS", "-4", "-L",
      "--connect-timeout", "7",
      "--max-time", String(Math.ceil(timeoutMs / 1000)),
      "-A", UA,
      "-H", "Accept: application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.2",
      "-w", "\n__STATUS__%{http_code}\n__URL__%{url_effective}\n__TYPE__%{content_type}\n",
      url,
    ];
    const { stdout } = await execFileAsync("curl", args, {
      timeout: timeoutMs + 3000,
      maxBuffer: MAX_BYTES + 1_000_000,
    });
    const text = String(stdout || "");
    const statusPos = text.lastIndexOf("__STATUS__");
    const urlPos = text.lastIndexOf("__URL__");
    const typePos = text.lastIndexOf("__TYPE__");
    if (statusPos < 0 || urlPos < 0 || typePos < 0) return null;
    const body = text.slice(0, statusPos).replace(/\n$/, "");
    const status = Number(text.slice(statusPos + "__STATUS__".length, text.indexOf("\n", statusPos + 1)).trim());
    const effective = text.slice(urlPos + "__URL__".length, text.indexOf("\n", urlPos + 1)).trim();
    const contentType = text.slice(typePos + "__TYPE__".length).trim();
    return {
      status: Number.isFinite(status) ? status : 0,
      url: effective || url,
      contentType,
      body,
      buf: Buffer.from(body, "utf8"),
      bytes: Buffer.byteLength(body, "utf8"),
    };
  } catch (err) {
    return { status: 0, url, contentType: "", body: "", buf: null, bytes: 0, error: err?.name || String(err) };
  }
}

async function waybackDomainIndex(base) {
  const wildcard = new URL("/*", base + "/").href;
  const endpoint = new URL("https://web.archive.org/cdx/search/cdx");
  endpoint.searchParams.set("url", wildcard);
  endpoint.searchParams.set("output", "json");
  endpoint.searchParams.set("filter", "statuscode:200");
  endpoint.searchParams.set("collapse", "urlkey");
  endpoint.searchParams.set("fl", "original,timestamp,mimetype,statuscode");
  endpoint.searchParams.set("limit", "2000");

  const r = await fetchBuffer(endpoint.href, ARCHIVE_TIMEOUT_MS, {
    "Accept": "application/json,text/plain;q=0.8,*/*;q=0.1",
  });
  if (r.status !== 200 || !r.buf) {
    return { endpoint: endpoint.href, status: r.status, candidates: [], error: r.error || null };
  }
  let rows = [];
  try {
    rows = JSON.parse(r.buf.toString("utf8"));
  } catch {
    return { endpoint: endpoint.href, status: r.status, candidates: [], error: "invalid_json" };
  }
  if (!Array.isArray(rows)) return { endpoint: endpoint.href, status: r.status, candidates: [] };

  const candidates = [];
  for (const row of rows.slice(1)) {
    if (!Array.isArray(row) || !row[0]) continue;
    const original = String(row[0]);
    if (!sameOrigin(original, base)) continue;
    if (!/google|merchant|shopping|feed|xml|woocommerce_gpf|woo-feed|wppfm|product-feed|feedcraft/i.test(original)) continue;
    const timestamp = String(row[1] || "");
    const mimetype = String(row[2] || "");
    candidates.push({
      url: original,
      timestamp,
      mimetype,
      archiveUrl: timestamp ? `https://web.archive.org/web/${timestamp}id_/${original}` : null,
      source: "internet-archive-cdx",
    });
  }
  return {
    endpoint: endpoint.href,
    status: r.status,
    candidateCount: candidates.length,
    candidates: [...new Map(candidates.map(x => [x.url, x])).values()],
  };
}

async function commonCrawlRecentIndexes(limit = 4) {
  const endpoint = "https://index.commoncrawl.org/collinfo.json";
  const r = await fetchBuffer(endpoint, ARCHIVE_TIMEOUT_MS, {
    "Accept": "application/json,text/plain;q=0.8,*/*;q=0.1",
  });
  if (r.status !== 200 || !r.buf) return [];
  try {
    const data = JSON.parse(r.buf.toString("utf8"));
    if (!Array.isArray(data)) return [];
    return data.slice(0, limit).map(item => {
      const raw = String(item?.id || item?.name || item?.["cdx-api"] || "").trim();
      if (!raw) return null;
      if (/^https?:\/\//i.test(raw)) {
        const last = raw.replace(/\/$/, "").split("/").pop() || "";
        return last.replace(/-index$/, "");
      }
      return raw.replace(/-index$/, "");
    }).filter(Boolean);
  } catch {
    return [];
  }
}

async function commonCrawlDomainIndex(base, collection) {
  if (!collection) return { status: 0, candidates: [], error: "no_collection" };
  const wildcard = new URL("/*", base + "/").href;
  const endpoint = new URL(`https://index.commoncrawl.org/${collection}-index`);
  endpoint.searchParams.set("url", wildcard);
  endpoint.searchParams.set("output", "json");
  endpoint.searchParams.set("fl", "url,timestamp,mime,status");
  endpoint.searchParams.set("filter", "status:200");
  endpoint.searchParams.set("collapse", "urlkey");
  endpoint.searchParams.set("limit", "2000");

  const r = await fetchBuffer(endpoint.href, ARCHIVE_TIMEOUT_MS, {
    "Accept": "application/json,text/plain;q=0.8,*/*;q=0.1",
  });
  if (r.status !== 200 || !r.buf) {
    return { endpoint: endpoint.href, status: r.status, candidates: [], error: r.error || null };
  }

  const candidates = [];
  for (const line of r.buf.toString("utf8").split(/\r?\n/)) {
    const s = line.trim();
    if (!s) continue;
    try {
      const row = JSON.parse(s);
      const original = String(row?.url || "");
      if (!sameOrigin(original, base)) continue;
      if (!/google|merchant|shopping|feed|xml|woocommerce_gpf|woo-feed|wppfm|product-feed|feedcraft/i.test(original)) continue;
      candidates.push({
        url: original,
        timestamp: String(row?.timestamp || ""),
        mimetype: String(row?.mime || row?.["mime-detected"] || ""),
        archiveSource: "common-crawl-cdxj",
        collection,
        warc: row?.filename || "",
        offset: row?.offset || "",
        length: row?.length || "",
      });
    } catch {}
  }
  return {
    endpoint: endpoint.href,
    status: r.status,
    candidateCount: candidates.length,
    candidates: [...new Map(candidates.map(x => [x.url, x])).values()],
  };
}

async function discoverLive(base) {
  const out = {
    urls: new Set(),
    pages: [],
    directories: [],
    wpJson: [],
    errors: [],
  };
  const paths = [
    "/robots.txt",
    "/sitemap.xml",
    "/wp-sitemap.xml",
    "/",
    "/shop/",
    "/products/",
    "/product-category/",
    "/wp-json/",
  ];
  for (const path of paths) {
    const url = new URL(path, base + "/").href;
    const r = await fetchBuffer(url, LIVE_TIMEOUT_MS);
    if (r.status !== 200 || !r.buf) {
      out.errors.push({ url, status: r.status, error: r.error || null, challenge: challengeLike(r.status, "") });
      continue;
    }
    const text = r.buf.toString("utf8");
    const links = parseLinks(text, url);
    for (const u of links) out.urls.add(u);
    out.pages.push({ url, finalUrl: r.url, status: r.status, bytes: r.bytes, links: links.length });
    if (path === "/wp-json/" && /^s*[\[{]/.test(text)) {
      try {
        const data = JSON.parse(text);
        for (const key of Object.keys(data?.routes || {})) {
          if (/feed|merchant|google|product-feed/i.test(key)) {
            out.wpJson.push({ route: key });
            const u = absoluteUrl(key, base);
            if (u) out.urls.add(u);
          }
        }
      } catch {}
    }
  }

  const dirPaths = [
    "/wp-content/uploads/woo-feed/",
    "/wp-content/uploads/woo-product-feed-pro/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/codesolz-feeds/",
  ];
  for (const path of dirPaths) {
    const url = new URL(path, base + "/").href;
    const r = await fetchBuffer(url, LIVE_TIMEOUT_MS);
    if (r.status !== 200 || !r.buf) {
      out.directories.push({ url, status: r.status, error: r.error || null });
      continue;
    }
    const links = parseLinks(r.buf.toString("utf8"), url, true)
      .filter(u => /\.xml(?:$|\?)/i.test(u) || /google|merchant|shopping|feed/i.test(u));
    for (const u of links) out.urls.add(u);
    out.directories.push({ url, status: r.status, bytes: r.bytes, links: links.length });
  }
  return {
    urls: [...out.urls],
    pages: out.pages,
    directories: out.directories,
    wpJson: out.wpJson,
    errors: out.errors,
  };
}

function candidateScore(url) {
  const u = String(url || "").toLowerCase();
  let score = 0;
  if (u.includes("woocommerce_gpf")) score += 100;
  if (u.includes("/wp-content/uploads/woo-product-feed-pro/")) score += 95;
  if (u.includes("/wp-content/uploads/woo-feed/")) score += 90;
  if (u.includes("/wp-content/uploads/wppfm-feeds/")) score += 85;
  if (u.includes("/feedcraft-product-feed/")) score += 80;
  if (u.includes("google")) score += 35;
  if (u.includes("merchant")) score += 30;
  if (u.includes("shopping")) score += 25;
  if (u.includes("feed")) score += 20;
  if (/\.xml(?:$|\?)/i.test(u)) score += 15;
  return score;
}

function takeCandidateWindow(values, max = 72) {
  return [...new Map(values.map(x => [String(x.url || ""), x])).values()]
    .sort((a, b) => candidateScore(b.url) - candidateScore(a.url))
    .slice(0, max);
}

async function verifyCandidate(url, base) {
  const observed = [];
  const f = await fetchBuffer(url);
  observed.push({
    transport: "node-fetch",
    status: f.status,
    finalUrl: f.url,
    contentType: f.contentType,
    bytes: f.bytes,
    error: f.error || null,
    challenge: challengeLike(f.status, f.buf ? f.buf.toString("utf8", 0, Math.min(f.buf.length, 12000)) : ""),
  });
  if (f.status === 200 && f.buf) {
    const body = f.buf.toString("utf8");
    if (looksGoogleMerchantXml(body, f.contentType)) {
      return { verified: true, source: "PUBLIC_NATIVE_FEED", transport: "node-fetch", finalUrl: f.url, body: f.buf, observed };
    }
  }

  await sleep(300);
  const c = await curlRaw(url);
  if (c) {
    const body = c.body || "";
    observed.push({
      transport: "curl-4",
      status: c.status,
      finalUrl: c.url,
      contentType: c.contentType,
      bytes: c.bytes,
      error: c.error || null,
      challenge: challengeLike(c.status, body),
    });
    if (c.status === 200 && looksGoogleMerchantXml(body, c.contentType)) {
      return { verified: true, source: "PUBLIC_NATIVE_FEED", transport: "curl-4", finalUrl: c.url, body: c.buf, observed };
    }
  }
  return { verified: false, observed };
}

async function fetchArchivedSnapshot(entry) {
  if (entry.archiveUrl) {
    const r = await fetchBuffer(entry.archiveUrl, ARCHIVE_TIMEOUT_MS, {
      "Accept": "application/xml,application/rss+xml,text/xml,text/html;q=0.8,*/*;q=0.1",
    });
    if (r.status === 200 && r.buf) {
      const body = r.buf.toString("utf8");
      if (looksGoogleMerchantXml(body, r.contentType) || /<(?:rss|feed)\b/i.test(body)) {
        return {
          status: r.status,
          finalUrl: r.url,
          contentType: r.contentType,
          bytes: r.bytes,
          body: r.buf,
          transport: "wayback",
        };
      }
    }
  }

  if (entry.warc && entry.offset !== "" && entry.length !== "") {
    try {
      const start = Number(entry.offset);
      const length = Number(entry.length);
      if (!Number.isFinite(start) || !Number.isFinite(length) || start < 0 || length <= 0 || length > MAX_BYTES) return null;
      const end = start + length - 1;
      const url = `https://data.commoncrawl.org/${entry.warc}`;
      const r = await fetchBuffer(url, ARCHIVE_TIMEOUT_MS, {
        "Range": `bytes=${start}-${end}`,
        "Accept": "application/octet-stream,*/*;q=0.1",
      });
      if (r.status !== 206 && r.status !== 200) return null;
      if (!r.buf) return null;
      let raw = r.buf;
      if (raw[0] === 0x1f && raw[1] === 0x8b) {
        const chunks = [];
        const gunzip = createGunzip();
        await new Promise((resolve, reject) => {
          gunzip.on("data", chunk => chunks.push(chunk));
          gunzip.on("end", resolve);
          gunzip.on("error", reject);
          Readable.from(raw).pipe(gunzip);
        });
        raw = Buffer.concat(chunks);
      }
      const text = raw.toString("utf8");
      const bodyStart = text.indexOf("\r\n\r\n");
      const body = bodyStart >= 0 ? text.slice(bodyStart + 4) : text;
      const buf = Buffer.from(body, "utf8");
      if (!looksGoogleMerchantXml(body, "application/xml") && !/<(?:rss|feed)\b/i.test(body)) return null;
      return {
        status: 200,
        finalUrl: entry.url,
        contentType: "application/xml",
        bytes: buf.length,
        body: buf,
        transport: "commoncrawl-warc",
      };
    } catch {
      return null;
    }
  }
  return null;
}

async function verifyMany(candidates, base, concurrency = 10) {
  const out = [];
  let index = 0;
  async function worker() {
    while (true) {
      const i = index++;
      if (i >= candidates.length) return;
      const candidate = candidates[i];
      const result = await verifyCandidate(candidate.url, base);
      out.push({ candidate, ...result });
    }
  }
  await Promise.all(Array.from({ length: Math.min(concurrency, candidates.length || 1) }, worker));
  return out;
}

async function recover([name, base], collections) {
  await mkdir(OUT + "/" + slug(name), { recursive: true });

  const result = {
    name,
    base,
    status: "UNRESOLVED",
    live_native_feed: null,
    historical_native_feed: null,
    live_candidate_count: 0,
    archive_candidate_count: 0,
    live_discovery: null,
    wayback: null,
    commoncrawl: null,
    observations: [],
  };

  const live = await discoverLive(base);

  const archiveBases = [base];
  try {
    const u = new URL(base);
    const altHost = u.hostname.startsWith("www.") ? u.hostname.slice(4) : `www.${u.hostname}`;
    const alt = new URL(u.href);
    alt.hostname = altHost;
    archiveBases.push(alt.origin);
  } catch {}
  const waybackResults = [];
  for (const archiveBase of archiveBases) {
    waybackResults.push(await waybackDomainIndex(archiveBase));
    await sleep(SLEEP_MS);
  }
  const wayback = {
    endpoint: waybackResults.map(x => x.endpoint).filter(Boolean).join("\n"),
    status: waybackResults.every(x => x.status === 200) ? 200 : waybackResults.find(x => x.status)?.status || 0,
    candidates: [...new Map(waybackResults.flatMap(x => x.candidates || []).map(x => [x.url, x])).values()],
  };

  const commonResults = [];
  for (const collection of collections || []) {
    commonResults.push(await commonCrawlDomainIndex(base, collection));
    await sleep(SLEEP_MS);
  }
  const commonCrawl = {
    collections: commonResults.map(x => x.collection).filter(Boolean),
    status: commonResults.every(x => x.status === 200 || x.status === 0) ? 200 : commonResults.find(x => x.status)?.status || 0,
    candidates: [...new Map(commonResults.flatMap(x => x.candidates || []).map(x => [x.url, x])).values()],
    queriedCollections: (collections || []).length,
  };

  result.live_discovery = live;
  result.wayback = wayback;
  result.commoncrawl = commonCrawl;

  const candidates = new Map();
  for (const path of KNOWN_PATHS) {
    const url = new URL(path, base + "/").href;
    candidates.set(url, { url, source: "known-pattern" });
  }
  for (const u of live.urls) candidates.set(u, { url: u, source: "live-discovery" });
  for (const x of wayback.candidates || []) candidates.set(x.url, x);
  for (const x of commonCrawl.candidates || []) candidates.set(x.url, x);

  const feedCandidates = takeCandidateWindow(
    [...candidates.values()].filter(x =>
      sameOrigin(x.url, base) &&
      /google|merchant|shopping|feed|xml|woocommerce_gpf|woo-feed|wppfm|product-feed|feedcraft/i.test(x.url)
    ),
    72
  );

  result.live_candidate_count = feedCandidates.length;
  result.archive_candidate_count = (wayback.candidates?.length || 0) + (commonCrawl.candidates?.length || 0);

  // Normal HTTP live verification: parallel candidates for this host, no proxy/evasion.
  const liveChecks = await verifyMany(feedCandidates, base, 10);
  for (const check of liveChecks) {
    result.observations.push({
      candidate: check.candidate.url,
      source: check.candidate.source || check.candidate.archiveSource || "candidate",
      verified: check.verified,
      observed: check.observed,
    });
  }
  const winning = liveChecks.find(x => x.verified);
  if (winning) {
    const hash = createHash("sha256").update(winning.body).digest("hex");
    const file = `${OUT}/feeds/${slug(name)}-native-${hash.slice(0, 12)}.xml`;
    await writeFile(file, winning.body);
    result.live_native_feed = {
      url: winning.candidate.url,
      finalUrl: winning.finalUrl,
      source: winning.source,
      transport: winning.transport,
      file,
      sha256: hash,
      bytes: winning.body.length,
    };
  }

  if (!result.live_native_feed) {
    const historical = takeCandidateWindow(
      [
        ...(wayback.candidates || []),
        ...(commonCrawl.candidates || []),
      ].filter(x => x.archiveUrl || x.warc),
      12
    );
    const archived = [];
    for (const entry of historical) {
      const snap = await fetchArchivedSnapshot(entry);
      if (!snap) continue;
      archived.push({ entry, snap });
    }
    const winningArchive = archived[0];
    if (winningArchive) {
      const { entry, snap } = winningArchive;
      const hash = createHash("sha256").update(snap.body).digest("hex");
      const file = `${OUT}/feeds/${slug(name)}-historical-${hash.slice(0, 12)}.xml`;
      await writeFile(file, snap.body);
      result.historical_native_feed = {
        originalUrl: entry.url,
        archiveUrl: entry.archiveUrl,
        capturedAt: entry.timestamp || null,
        archiveSource: entry.source || entry.archiveSource || "archive",
        file,
        sha256: hash,
        bytes: snap.bytes,
        note: "Historical public Merchant XML. This does not establish that the same feed is live today.",
      };
    }
  }

  if (result.live_native_feed) {
    result.status = "VERIFIED_LIVE_NATIVE_FEED";
  } else if (result.historical_native_feed) {
    result.status = "VERIFIED_HISTORICAL_NATIVE_FEED";
  } else {
    const accessFailures = result.observations.filter(x => x.observed?.some(o =>
      o.challenge || Number(o.status) === 403 || Number(o.status) === 429
    )).length;
    const archiveAvailable = result.archive_candidate_count > 0;
    if (archiveAvailable && accessFailures) result.status = "HISTORICAL_CANDIDATE_LIVE_ACCESS_BLOCKED";
    else if (accessFailures) result.status = "PUBLIC_ACCESS_BLOCKED_OR_UNVERIFIED";
    else result.status = "NO_VERIFIED_PUBLIC_NATIVE_FEED";
  }

  await writeFile(
    `${OUT}/${slug(name)}/report.json`,
    JSON.stringify(result, null, 2) + "\n"
  );
  return result;
}

async function main() {
  await mkdir(OUT + "/feeds", { recursive: true });

  const argv = process.argv.slice(2);
  const args = {};
  for (let i = 0; i < argv.length; i++) {
    const token = argv[i];
    if (!token.startsWith("--")) continue;
    const key = token.slice(2);
    const next = argv[i + 1];
    args[key] = next && !next.startsWith("--") ? argv[++i] : true;
  }

  if (args["site-name"] && args["site-url"]) {
    const collections = await commonCrawlRecentIndexes(4);
    const result = await recover([String(args["site-name"]), String(args["site-url"])], collections);
    const summary = {
      schema_version: "woocommerce-google-feed-archive-recovery/v1-single-site",
      generated_at: new Date().toISOString(),
      commoncrawl_collections: collections,
      targets: 1,
      site: {
        name: result.name,
        base: result.base,
        status: result.status,
        live: result.live_native_feed,
        historical: result.historical_native_feed,
        archive_candidate_count: result.archive_candidate_count,
        live_candidate_count: result.live_candidate_count,
      },
    };
    await writeFile(OUT + "/summary.json", JSON.stringify(summary, null, 2) + "\n");
    console.log(JSON.stringify(summary, null, 2));
    return;
  }

  const collections = await commonCrawlRecentIndexes(4);
  const results = [];
  for (const target of TARGETS) {
    results.push(await recover(target, collections));
    await sleep(SLEEP_MS);
  }

  const summary = {
    schema_version: "woocommerce-google-feed-archive-recovery/v1",
    generated_at: new Date().toISOString(),
    commoncrawl_collections: collections,
    targets: results.length,
    live_native_verified: results.filter(x => x.status === "VERIFIED_LIVE_NATIVE_FEED").length,
    historical_native_verified: results.filter(x => x.status === "VERIFIED_HISTORICAL_NATIVE_FEED").length,
    historical_candidates_blocked: results.filter(x => x.status === "HISTORICAL_CANDIDATE_LIVE_ACCESS_BLOCKED").length,
    statuses: Object.groupBy(results, x => x.status),
    feeds: results.map(x => ({
      name: x.name,
      status: x.status,
      live: x.live_native_feed,
      historical: x.historical_native_feed,
      archive_candidate_count: x.archive_candidate_count,
      live_candidate_count: x.live_candidate_count,
    })),
  };
  await writeFile(OUT + "/summary.json", JSON.stringify(summary, null, 2) + "\n");
  await writeFile(OUT + "/audit.json", JSON.stringify({ collections, results }, null, 2) + "\n");
  console.log(JSON.stringify(summary, null, 2));
}

main().catch(err => {
  console.error(err);
  process.exitCode = 1;
});
