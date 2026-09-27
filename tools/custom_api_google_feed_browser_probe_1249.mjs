#!/usr/bin/env node
import fs from "node:fs/promises";
import { chromium } from "playwright";

const NAV_TIMEOUT = 25000;
const SETTLE_MS = 6000;
const MAX_BODY = 900000;
const MAX_RESPONSES = 300;
const CONCURRENCY = 4;
const googleNs = /base\.google\.com\/ns\/1\.0/i;
const itemTag = /<(?:item|entry)\b/i;
const coreField = /<(?:g:)?(?:id|title|link|price|availability|condition|brand|gtin|mpn)\b/i;

function validateXml(status, contentType, body) {
  if (status !== 200 || !body) return null;
  if (!/(?:xml|rss|atom)/i.test(contentType) && !/^\s*<\?xml|^\s*<(?:rss|feed)\b/i.test(body)) return null;
  if (!googleNs.test(body) || !itemTag.test(body) || !coreField.test(body)) return null;
  const count = (body.match(/<(?:item|entry)\b/g) || []).length;
  return count ? { status, content_type: contentType, bytes: Buffer.byteLength(body), item_count_observed: count, google_namespace: "http://base.google.com/ns/1.0", validation: "strict_google_merchant_xml" } : null;
}

function likelyInteresting(url) {
  return /(?:feed|merchant|shopping|google|productfeed|datafeed|catalogfeed|rss|atom|graphql|api(?:\/|$)|secure\/api|rest\/|_next\/data)/i.test(url);
}
function sleep(ms){ return new Promise(r=>setTimeout(r,ms)); }

async function mapLimit(items, fn, limit=CONCURRENCY) {
  const out = new Array(items.length); let cursor = 0;
  async function worker() {
    while (true) {
      const i = cursor++; if (i >= items.length) return;
      out[i] = await fn(items[i], i);
    }
  }
  await Promise.all(Array.from({length: Math.min(limit, items.length)}, worker));
  return out;
}

async function probeSite(browser, site) {
  const roots = [];
  for (const root of site.roots) {
    const context = await browser.newContext({
      userAgent: "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
    });
    const page = await context.newPage();
    const network = [];
    const verified = [];
    const feeds = [];
    const api = [];
    const errors = [];

    const onResponse = async response => {
      if (network.length >= MAX_RESPONSES) return;
      const req = response.request();
      const type = req.resourceType();
      const url = response.url();
      const row = {
        url, status: response.status(),
        content_type: response.headers()["content-type"] || "",
        resource_type: type
      };
      network.push(row);
      if (likelyInteresting(url) || /xml|rss|atom|json/i.test(row.content_type)) {
        if (likelyInteresting(url)) feeds.push(url);
        try {
          if (response.status() === 200 && /xml|rss|atom/i.test(row.content_type)) {
            const body = await response.text();
            const v = validateXml(response.status(), row.content_type, body);
            if (v) verified.push({ url, final_url: url, ...v });
          }
        } catch {}
        if (response.status() === 200 && /json/i.test(row.content_type)) {
          api.push({url, status:row.status, content_type:row.content_type, resource_type:type});
        }
      }
    };
    page.on("response", onResponse);
    page.on("requestfailed", request => {
      if (errors.length < 30) errors.push({url:request.url(),resource_type:request.resourceType(),error:request.failure()?.errorText||"request_failed"});
    });

    let navigation = null;
    try {
      const response = await page.goto(root, {waitUntil:"domcontentloaded",timeout:NAV_TIMEOUT});
      navigation = {
        requested_url: root,
        final_url: page.url(),
        status: response?.status() ?? null,
        content_type: response?.headers()?.["content-type"] || ""
      };
      await sleep(SETTLE_MS);
    } catch (e) {
      navigation = {requested_url:root, final_url:page.url(), status:null, error:String(e)};
    }

    // Pull same-origin script text only where the browser loaded an explicit JS resource.
    const scripts = [...new Set(network.filter(x => x.resource_type === "script" && /\.(?:m?js)(?:\?|$)/i.test(x.url)).map(x=>x.url))].slice(0,30);
    const scriptHints = [];
    for (const u of scripts.slice(0,12)) {
      try {
        const rr = await page.request.get(u,{timeout:12000});
        if (!rr.ok()) continue;
        const text = await rr.text();
        for (const m of text.matchAll(/(?:https?:\/\/[^"'\\s<>]+|\/(?:api|graphql|rest|secure\/api|feeds?|google[^"'\\s<>]{0,80}|merchant[^"'\\s<>]{0,80}|shopping[^"'\\s<>]{0,80})[^"'\\s<>]*)/gi)) {
          scriptHints.push(m[0].slice(0,500));
          if (scriptHints.length >= 120) break;
        }
      } catch {}
      if (scriptHints.length >= 120) break;
    }

    await context.close();
    roots.push({
      root, navigation,
      verified_google_xml: verified,
      candidate_urls: [...new Set(feeds)].slice(0,200),
      public_json_requests: [...new Map(api.map(x=>[x.url,x])).values()].slice(0,100),
      script_hints: [...new Set(scriptHints)].slice(0,120),
      network_requests: network.slice(0,MAX_RESPONSES),
      request_failures: errors
    });
  }
  return {
    name: site.name,
    roots: site.roots,
    verified_google_xml: roots.flatMap(x=>x.verified_google_xml),
    roots_results: roots
  };
}

async function main() {
  const [registryPath, outputPath] = process.argv.slice(2);
  const input = JSON.parse(await fs.readFile(registryPath, "utf8"));
  const browser = await chromium.launch({headless:true});
  try {
    const results = await mapLimit(input.sites, s=>probeSite(browser,s));
    const verified = results.flatMap(s=>s.verified_google_xml.map(v=>({...v,site:s.name})));
    const report = {
      schema_version: "foundation-custom-api-google-browser-live/v1",
      issue: 1249,
      generated_on: new Date().toISOString(),
      sites: results.length,
      verified_google_xml: verified,
      results
    };
    await fs.writeFile(outputPath, JSON.stringify(report,null,2));
    console.log(JSON.stringify({
      schema_version: report.schema_version,
      sites: report.sites,
      verified_feed_count: verified.length,
      verified_feeds: verified
    }, null, 2));
  } finally {
    await browser.close();
  }
}
main().catch(e=>{ console.error(e); process.exit(1); });
