import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_identified_family_guess_v5.mjs","utf8");
test("confirmed standalone scope only",()=>{
  assert.match(s,/confirmed-standalone-only/);
  assert.doesNotMatch(s,/unknown20|unknown_woocommerce/);
  assert.doesNotMatch(s,/wc\/store\/v1\/products/);
});
test("researched families",()=>{
  for(const x of ["woocommerce_gpf=google","woo_feed=","woo-feed/google/xml","woo-product-feed-pro/xml","wppfm-feeds","Google-Products-New.xml","google_shopping_ctx_1.xml","listings07.xml","merchantcenter2.xml"]) assert.ok(s.includes(x),x);
});
test("Wayback and directory recovery exist",()=>{
  assert.match(s,/web\.archive\.org\/cdx\/search\/cdx/);
  assert.match(s,/current-directory-index/);
  assert.match(s,/wayback-reference/);
});
test("no product or browser extraction is implemented",()=>{
  assert.doesNotMatch(s,/playwright\.launch|async_playwright/i);
  assert.doesNotMatch(s,/wc\/store\/v1\/products/);
});
test("strict native gate",()=>{
  assert.match(s,/function native\(body\)/);
  assert.match(s,/sameHost\(r\.final_url,site\.root\)/);
  assert.ok(s.includes('["id","title","link","price"]'));
});
