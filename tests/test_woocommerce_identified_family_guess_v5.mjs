import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_identified_family_guess_v5.mjs","utf8");
test("identified standalone scope",()=>{
  for(const x of ["PC Studio","Quickin Computers","Avikaretails","IT Gadgets Online","Prime ABGB","Kryptronix Gaming","NCL Computer"]) assert.ok(s.includes(x),x);
  assert.doesNotMatch(s,/unknown20|unknown_woocommerce/);
  assert.doesNotMatch(s,/wc\/store\/v1\/products/);
});
test("researched family grammars",()=>{
  for(const x of ["woocommerce_gpf=google","woo_feed=","woo-feed/google/xml","woo-product-feed-pro/xml","wppfm-feeds","Google-Products-New.xml","webtoffee_product_feed","wt_google_Feed.xml"]) assert.ok(s.includes(x),x);
});
test("historical and directory recovery",()=>{
  assert.match(s,/web\.archive\.org\/cdx\/search\/cdx/);
  assert.match(s,/current-directory-index/);
  assert.match(s,/wayback-reference/);
});
test("no product/browser extraction",()=>{
  assert.doesNotMatch(s,/playwright\.launch|async_playwright/i);
  assert.doesNotMatch(s,/wc\/store\/v1\/products/);
});
test("strict native gate",()=>{
  assert.match(s,/function native\(body\)/);
  assert.match(s,/sameHost\(r\.final_url,site\.root\)/);
  assert.ok(s.includes('["id","title","link","price"]'));
});
