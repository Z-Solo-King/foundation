import { mkdir, writeFile } from "node:fs/promises";

const root = (process.env.ROOT || "").replace(/\/$/, "");
const site = process.env.SITE_NAME || root;
const outDir = "artifacts/google-feed";
const ua = "Mozilla/5.0 (compatible; FoundationGoogleFeedMatrix/1.0)";

const paths = [
  "/google.xml","/google.rss","/google.rss.xml",
  "/google-feed","/google-feed.xml","/google_feed.xml",
  "/google-shopping","/google-shopping.xml",
  "/google-shopping-feed","/google-shopping-feed.xml",
  "/google-products.xml","/google-product.xml","/google-product-feed.xml",
  "/google_product_feed.xml","/google_products.xml",
  "/googlebase.xml","/google_base.xml","/google-base.xml",
  "/googlemerchant.xml","/google-merchant.xml",
  "/merchant.xml","/merchant-feed","/merchant-feed.xml","/merchant_feed.xml",
  "/product-feed","/product-feed.xml","/product_feed.xml",
  "/products-feed","/products-feed.xml","/products_feed.xml",
  "/shopping.xml","/shopping-feed.xml",
  "/feed.xml","/feed/google.xml","/feed/google-shopping.xml","/feed/google-shopping-feed.xml",
  "/feeds/google.xml","/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml",
  "/feeds/google_base.xml","/feeds/products.xml",
  "/feed/products.xml","/feed/product-feed.xml",
  "/catalog/feed.xml","/catalog/google.xml","/media/feed/google.xml",
  "/products.rss","/feeds/products.rss","/rss.xml"
];

async function get(url, accept="*/*") {
  const c = new AbortController();
  const timer = setTimeout(() => c.abort(), 12000);
  try {
    const res = await fetch(url, {
      redirect: "follow",
      signal: c.signal,
      headers: { "User-Agent": ua, "Accept": accept }
    });
    const text = await res.text();
    return {
      requested_url: url,
      final_url: res.url,
      status: res.status,
      content_type: res.headers.get("content-type") || "",
      bytes: Buffer.byteLength(text),
      body: text
    };
  } catch (e) {
    return {
      requested_url: url, final_url: "", status: 0, content_type: "",
      bytes: 0, body: "", error: String(e)
    };
  } finally {
    clearTimeout(timer);
  }
}

function isGoogleXml(body) {
  if (!body) return false;
  const head = body.slice(0, 12000).toLowerCase();
  const xml = /<\?xml|<rss\b|<feed\b|<item\b/.test(head);
  const gns = /base\.google\.com\/ns\/1\.0/.test(head);
  const gfields = /<g:(id|title|link|price|availability)\b/.test(head);
  const items = body.match(/<item\b[\s\S]*?<\/item>/gi) || body.match(/<entry\b[\s\S]*?<\/entry>/gi) || [];
  if (!xml || (!gns && !gfields) || items.length < 1) return false;
  const first = items.slice(0, 10);
  const good = first.filter(x =>
    /<g:id\b/i.test(x) &&
    /<g:title\b/i.test(x) &&
    /<g:link\b/i.test(x) &&
    /<g:price\b/i.test(x)
  ).length;
  return good >= Math.max(1, Math.ceil(first.length * 0.5));
}

function extractUrls(body) {
  const found = new Set();
  const re = /(?:https?:\/\/[^"'<>\s]+|\/[^"'<>\s]+)/g;
  for (const x of body.match(re) || []) {
    if (/feed|google|merchant|shopping|\.xml(?:$|[?#])/i.test(x)) {
      found.add(x.replace(/[),.;]+$/, ""));
    }
  }
  return [...found].slice(0, 200);
}

async function main() {
  await mkdir(outDir, { recursive: true });
  const meta = {};
  for (const p of ["/robots.txt","/sitemap.xml"]) {
    const r = await get(root + p, "text/plain,application/xml,text/xml,*/*");
    meta[p] = {
      status: r.status, final_url: r.final_url, content_type: r.content_type,
      bytes: r.bytes, feed_urls: extractUrls(r.body)
    };
  }

  const homepage = await get(root + "/", "text/html,*/*");
  meta["homepage"] = {
    status: homepage.status, final_url: homepage.final_url,
    content_type: homepage.content_type, bytes: homepage.bytes,
    feed_urls: extractUrls(homepage.body),
    app_signals: (homepage.body.match(/(?:simprosys|adnabu|mulwi|datafeedwatch|flexify|feednexa|feedforge|google shopping|merchant center|merchant feed)/gi) || []).slice(0,50)
  };

  const candidates = [];
  for (let i = 0; i < paths.length; i += 8) {
    const chunk = paths.slice(i, i + 8);
    const rs = await Promise.all(chunk.map(p => get(root + p, "application/xml,text/xml,application/rss+xml,application/atom+xml,*/*")));
    for (const r of rs) {
      const google = isGoogleXml(r.body);
      candidates.push({
        url: r.requested_url, final_url: r.final_url, status: r.status,
        content_type: r.content_type, bytes: r.bytes, google_xml: google,
        error: r.error || ""
      });
      if (google) {
        const safe = r.requested_url.replace(/^https?:\/\//,"").replace(/[^a-z0-9]+/gi,"_");
        await writeFile(`${outDir}/${safe}.xml`, r.body);
      }
    }
  }

  const verified = candidates.filter(x => x.google_xml);
  const result = {
    schema_version: "foundation-google-feed-matrix/v1",
    generated_on: new Date().toISOString(),
    site, root,
    candidates_tested: candidates.length,
    verified_google_xml: verified,
    robots: meta["/robots.txt"],
    sitemap: meta["/sitemap.xml"],
    homepage: meta["homepage"],
    status_counts: candidates.reduce((m,x)=>(m[x.status]=(m[x.status]||0)+1,m),{})
  };
  const slug = site.toLowerCase().replace(/[^a-z0-9]+/g,"-");
  await writeFile(`${outDir}/${slug}.json`, JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({
    site, root, candidates_tested: candidates.length,
    verified_google_xml: verified.map(x => x.url),
    status_counts: result.status_counts
  }, null, 2));
}

main().catch(e => { console.error(e); process.exit(1); });
