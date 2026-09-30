import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source = fs.readFileSync(path.resolve("tools/woocommerce_plugin_family_guess_v4.mjs"), "utf8");

test("wave 2 stays guess-only", () => {
  assert.match(source, /plugin-family-specific-xml-guess-only/);
  assert.doesNotMatch(source, /wc\/store\/v1\/products/);
  assert.doesNotMatch(source, /from ["']playwright["']/i);
  assert.doesNotMatch(source, /chromium\.launch|firefox\.launch|webkit\.launch/i);
});

test("research-expanded family grammars are present", () => {
  for (const s of [
    "listings07.xml",
    "google_shopping_ctx_1.xml",
    "Google-Products-New.xml",
    "wt_fb_Feed.xml",
    "feed-15364.xml",
    "klp-feeds-xml",
    "feed-xml-0.xml"
  ]) assert.ok(source.includes(s), s);
});

test("native validator implementation is present", () => {
  assert.match(source, /function strictValidate\(body\)/);
  assert.match(source, /base\\\.google\\\.com/);
  assert.ok(source.includes('const required = ["id","title","link","price"]'));
  assert.match(source, /validItems/);
  assert.match(source, /sameHost\(finalUrl, url\)/);
});
