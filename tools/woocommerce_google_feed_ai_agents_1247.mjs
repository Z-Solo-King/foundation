import { mkdir, writeFile } from "node:fs/promises";

const TARGETS = [
  ["ithunt","https://ithunt.in"],
  ["kccomputers","https://kccomputers.co.in"],
  ["KRG KART","https://krgkart.com"],
  ["PC Kumar Infotech","https://pckumar.in"],
  ["PCHubShop","https://www.pchubshop.com"],
  ["SCL Gaming","https://sclgaming.in"],
  ["Variety Infotech","https://varietyinfotech.com"],
  ["Moskeys","https://moskeys.com"],
  ["Theproaudio","https://www.theproaudio.com"]
];

const KNOWN = [
  "/?woocommerce_gpf=google",
  "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
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
  "/wp-content/uploads/codesolz-feeds/google-products.xml",
  "/wp-content/uploads/woo-feed/google/xml/google.xml",
  "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
  "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
  "/wp-content/uploads/wppfm-feeds/google.xml",
  "/wp-json/feedcraft-product-feed/v1/xml"
];

const OUT = "out/rescue-fast/ai_candidates.json";
await mkdir("out/rescue-fast", { recursive: true });

function extractPaths(text, base) {
  const out = new Set();
  const s = String(text || "");
  for (const m of s.matchAll(/https?:\/\/[^\\s<>"'\\)\\]]+|\/(?:[A-Za-z0-9._~:/?#\\[\\]@!$&'()*+,;=%-]+)/g)) {
    let raw = String(m[0]).replace(/[),.;]+$/, "");
    try {
      const u = new URL(raw, base);
      const path = u.pathname + (u.search || "");
      if (u.origin === new URL(base).origin &&
          path.length <= 500 &&
          (/xml|feed|merchant|google|shopping|product|woo|wppfm|codesolz|feedcraft/i.test(path))) {
        out.add(path);
      }
    } catch {}
  }
  return [...out];
}

async function groq() {
  if (!process.env.GROQ_API_KEY) return { provider: "groq", available: false, reason: "GROQ_API_KEY not configured" };
  const prompt = `Act as a public-web feed discovery agent. Investigate these nine Indian WooCommerce retailers for Google Merchant XML product-feed endpoints. Search current web/indexed references and retailer pages using your available browser/web-search tools. Do NOT bypass Cloudflare/CAPTCHA/authentication or suggest evasive techniques. Return candidate URLs/paths only; candidates are hints and will be verified separately. Do not label anything verified.

Retailers:
${TARGETS.map(([n,u]) => `- ${n}: ${u}`).join("\n")}

Known patterns already tested; find additional variants, plugin-specific paths, uploaded-feed directories, feed-generator endpoints, public sitemap/robots references, and publicly indexed historical feed URLs. Prefer exact URLs when evidence exists. Return concise text grouped by retailer.`;
  try {
    const r = await fetch("https://api.groq.com/openai/v1/chat/completions", {
      method: "POST",
      headers: { "Authorization": `Bearer ${process.env.GROQ_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify({
        model: process.env.GROQ_AGENT_MODEL || "openai/gpt-oss-120b",
        messages: [{ role: "user", content: prompt }],
        temperature: 0.1,
        max_completion_tokens: 6000
      })
    });
    const data = await r.json();
    return { provider: "groq", available: r.ok, status: r.status, model: process.env.GROQ_AGENT_MODEL || "openai/gpt-oss-120b", text: data?.choices?.[0]?.message?.content || "", error: r.ok ? null : (data?.error?.message || "request_failed") };
  } catch (e) {
    return { provider: "groq", available: false, reason: e?.name || String(e) };
  }
}

async function gemini() {
  if (!process.env.GEMINI_API_KEY) return { provider: "gemini", available: false, reason: "GEMINI_API_KEY not configured" };
  const prompt = `Act as an independent feed-infrastructure analyst. For these nine Indian WooCommerce retailers, infer additional PUBLIC Google Merchant XML feed URL/path candidates from WordPress/WooCommerce feed-plugin conventions, indexed references and known hosting patterns. Do not propose bypassing anti-bot controls. Candidates are only hypotheses and will be independently verified. Return concise retailer-grouped URLs/paths.

${TARGETS.map(([n,u]) => `- ${n}: ${u}`).join("\n")}

Already-tested families include woocommerce_gpf, google.xml, product-feed.xml, feed/google.xml, feeds/google-products.xml, codesolz-feeds, woo-feed, woo-product-feed-pro, wppfm-feeds and FeedCraft.`;
  const model = process.env.GEMINI_MODEL || "gemini-3.5-flash";
  try {
    const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`, {
      method: "POST",
      headers: { "x-goog-api-key": process.env.GEMINI_API_KEY, "Content-Type": "application/json" },
      body: JSON.stringify({ contents: [{ parts: [{ text: prompt }] }] })
    });
    const data = await r.json();
    return { provider: "gemini", available: r.ok, status: r.status, model, text: data?.candidates?.[0]?.content?.parts?.map(x => x.text || "").join("\n") || "", error: r.ok ? null : (data?.error?.message || "request_failed") };
  } catch (e) {
    return { provider: "gemini", available: false, reason: e?.name || String(e) };
  }
}

const [g, m] = await Promise.all([groq(), gemini()]);
const providers = [g, m];
const retailers = TARGETS.map(([name, base]) => {
  const paths = new Set();
  for (const p of providers) {
    for (const path of extractPaths(p.text, base)) paths.add(path);
  }
  return { name, base, paths: [...paths].filter(p => !KNOWN.includes(p)).slice(0, 80) };
});
await writeFile(OUT, JSON.stringify({
  schema_version: "woocommerce-google-feed-ai-candidates/v1",
  generated_at: new Date().toISOString(),
  policy: "candidate discovery only; every candidate requires independent public verification",
  providers: providers.map(p => ({ provider:p.provider, available:p.available, status:p.status || null, model:p.model || null, reason:p.reason || null, error:p.error || null })),
  retailers
}, null, 2) + "\n");
console.log(JSON.stringify({ providers: providers.map(p => ({provider:p.provider,available:p.available,status:p.status||null})), retailers: retailers.map(r => ({name:r.name,count:r.paths.length})) }, null, 2));
