import { mkdir, writeFile } from "node:fs/promises";

const site = process.env.SITE_NAME || "unknown";
const roots = (process.env.ROOTS || "").split(",").map(x => x.trim().replace(/\/$/,"")).filter(Boolean);
const outDir = "artifacts/google-feed-deep";
const ua = "Mozilla/5.0 (compatible; FoundationGoogleFeedDeep/1.0)";

const genericPaths = [
  "/google.xml","/google.rss","/google.rss.xml","/google-feed","/google-feed.xml","/google_feed.xml",
  "/google-shopping","/google-shopping.xml","/google-shopping-feed","/google-shopping-feed.xml",
  "/google-products.xml","/google-product.xml","/google-product-feed.xml","/google_product_feed.xml",
  "/google_products.xml","/googlebase.xml","/google_base.xml","/google-base.xml","/googlemerchant.xml",
  "/google-merchant.xml","/merchant.xml","/merchant-feed","/merchant-feed.xml","/merchant_feed.xml",
  "/product-feed","/product-feed.xml","/product_feed.xml","/products-feed","/products-feed.xml",
  "/products_feed.xml","/shopping.xml","/shopping-feed.xml","/feed.xml","/feed/google.xml",
  "/feed/google-shopping.xml","/feed/google-shopping-feed.xml","/feeds/google.xml",
  "/feeds/google-shopping.xml","/feeds/google-shopping-feed.xml","/feeds/google_base.xml",
  "/feeds/products.xml","/feed/products.xml","/feed/product-feed.xml","/catalog/feed.xml",
  "/catalog/google.xml","/media/feed/google.xml","/products.rss","/feeds/products.rss",
  "/sitemap_products.xml","/sitemap-product.xml","/product-sitemap.xml","/sitemap_products_1.xml",
  "/sitemap/sitemap.xml","/sitemap_index.xml","/sitemap-index.xml"
];

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function get(url, accept="*/*") {
  const c = new AbortController();
  const timer = setTimeout(() => c.abort(), 12000);
  try {
    const res = await fetch(url, {
      redirect: "follow", signal: c.signal,
      headers: { "User-Agent": ua, "Accept": accept }
    });
    const body = await res.text();
    return {
      requested_url:url, final_url:res.url, status:res.status,
      content_type:res.headers.get("content-type")||"", bytes:Buffer.byteLength(body), body
    };
  } catch (e) {
    return {requested_url:url,final_url:"",status:0,content_type:"",bytes:0,body:"",error:String(e)};
  } finally { clearTimeout(timer); }
}

async function concurrent(urls, fn, width=8) {
  const out=[];
  for (let i=0;i<urls.length;i+=width) {
    const part=await Promise.all(urls.slice(i,i+width).map(fn));
    out.push(...part);
  }
  return out;
}

function isGoogleXml(body) {
  if (!body) return false;
  const head=body.slice(0,20000);
  if (!/(<rss\b|<feed\b|<item\b)/i.test(head)) return false;
  if (!/(base\.google\.com\/ns\/1\.0|<g:(id|title|link|price|availability)\b)/i.test(head)) return false;
  const items=body.match(/<item\b[\s\S]*?<\/item>/gi)||body.match(/<entry\b[\s\S]*?<\/entry>/gi)||[];
  if (!items.length) return false;
  const sample=items.slice(0,20);
  const good=sample.filter(x=>
    /<g:id\b/i.test(x)&&/<g:title\b/i.test(x)&&/<g:link\b/i.test(x)&&/<g:price\b/i.test(x)
  ).length;
  return good>=Math.max(1,Math.ceil(sample.length*0.5));
}

function extractUrls(body, baseUrl) {
  const found=new Set();
  const add=(raw)=>{
    try {
      const u=new URL(raw,baseUrl);
      if (/feed|google|merchant|shopping|superfeed|\.xml(?:$|[?#])/i.test(u.href)) found.add(u.href);
    } catch {}
  };
  for (const m of body.matchAll(/(?:https?:\/\/[^"'<>\s]+|\/[^"'<>\s]+)/g)) add(m[0].replace(/[),.;]+$/,""));
  return [...found].slice(0,250);
}

function extractLocs(body) {
  return [...body.matchAll(/<loc>\s*([^<]+?)\s*<\/loc>/gi)].map(m=>m[1].trim()).filter(Boolean);
}

async function main() {
  await mkdir(outDir,{recursive:true});
  const all=[];
  const discovery={};

  for (const root of roots) {
    const home=await get(root+"/","text/html,*/*");
    const robots=await get(root+"/robots.txt","text/plain,application/xml,*/*");
    const sitemapSeeds=[root+"/sitemap.xml",root+"/sitemap_index.xml",root+"/sitemap-index.xml",root+"/sitemap/sitemap.xml",root+"/sitemap_products.xml"];
    const sitemapResults=await concurrent([...new Set([...(robots.body.match(/^\s*Sitemap:\s*(\S+)/gim)||[]).map(x=>x.replace(/^\s*Sitemap:\s*/i,"")),...sitemapSeeds])],u=>get(u,"application/xml,text/xml,*/*"),6);

    const discovered=new Set();
    for (const source of [home,robots,...sitemapResults]) {
      for (const u of extractUrls(source.body,source.final_url||root+"/")) discovered.add(u);
    }

    const sitemapQueue=[];
    for (const r of sitemapResults) {
      if (r.status===200 && /xml/i.test(r.content_type+r.body.slice(0,200))) {
        for (const u of extractLocs(r.body)) {
          if (/(sitemap|\.xml)/i.test(u)) sitemapQueue.push(u);
          if (/feed|google|merchant|shopping|superfeed|\.xml(?:$|[?#])/i.test(u)) discovered.add(u);
        }
      }
    }

    const nested=[...new Set(sitemapQueue)].slice(0,30);
    const nestedResults=await concurrent(nested,u=>get(u,"application/xml,text/xml,*/*"),6);
    for (const r of nestedResults) {
      for (const u of extractLocs(r.body)) {
        if (/feed|google|merchant|shopping|superfeed|\.xml(?:$|[?#])/i.test(u)) discovered.add(u);
      }
    }

    const scripts=[...home.body.matchAll(/<script[^>]+src\s*=\s*["']([^"']+)["']/gi)]
      .map(m=>{try{return new URL(m[1],home.final_url||root+"/").href}catch{return ""}})
      .filter(Boolean).slice(0,40);

    const scriptResults=await concurrent([...new Set(scripts)],u=>get(u,"text/javascript,application/javascript,*/*"),6);
    for (const r of scriptResults) {
      for (const u of extractUrls(r.body,r.final_url||root+"/")) discovered.add(u);
    }

    discovery[root]={
      homepage:{status:home.status,bytes:home.bytes,urls:extractUrls(home.body,home.final_url||root+"/")},
      robots:{status:robots.status,bytes:robots.bytes,urls:extractUrls(robots.body,robots.final_url||root+"/")},
      sitemap_results:sitemapResults.map(r=>({url:r.requested_url,status:r.status,content_type:r.content_type,bytes:r.bytes})),
      nested_sitemaps:nestedResults.map(r=>({url:r.requested_url,status:r.status,bytes:r.bytes})),
      script_count:scripts.length,
      discovered_feedish_urls:[...discovered].slice(0,250)
    };

    const candidateUrls=[...new Set([...genericPaths.map(p=>root+p),...discovered])].slice(0,120);
    const results=await concurrent(candidateUrls,u=>get(u,"application/xml,text/xml,application/rss+xml,application/atom+xml,*/*"),8);
    for (const r of results) {
      const google=isGoogleXml(r.body);
      const row={site,root,url:r.requested_url,final_url:r.final_url,status:r.status,content_type:r.content_type,bytes:r.bytes,google_xml:google,error:r.error||""};
      all.push(row);
      if (google) {
        const safe=r.requested_url.replace(/^https?:\/\//,"").replace(/[^a-z0-9]+/gi,"_");
        await writeFile(`${outDir}/${safe}.xml`,r.body);
      }
    }
  }

  const verified=all.filter(x=>x.google_xml);
  const result={schema_version:"foundation-google-feed-deep/v1",generated_on:new Date().toISOString(),site,roots,candidates_tested:all.length,verified_google_xml:verified,discovery,status_counts:all.reduce((m,x)=>(m[x.status]=(m[x.status]||0)+1,m),{})};
  const slug=site.toLowerCase().replace(/[^a-z0-9]+/g,"-");
  await writeFile(`${outDir}/${slug}.json`,JSON.stringify(result,null,2)+"\n");
  console.log(JSON.stringify({site,roots,candidates_tested:all.length,verified_google_xml:verified.map(x=>x.url),status_counts:result.status_counts},null,2));
}

main().catch(e=>{console.error(e);process.exit(1)});
