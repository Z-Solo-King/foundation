import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_unknown_family_guess_v6.mjs","utf8");
test("true unknown scope",()=>{
  for(const x of ["Aarna Computers","Ads Store","Variety Infotech"]) assert.ok(s.includes(x),x);
  for(const x of ["Kryptronix Gaming","Prime ABGB","NCL Computer"]) assert.equal(s.includes(x),false,x);
});
test("identified family grammar coverage",()=>{
  for(const x of ["woocommerce_gpf=google","woo_feed=","wppfm-feeds","webtoffee_product_feed","codesolz-feeds","feedcraft-product-feed","rex-feed","klp-feeds-xml","feed-xml-0.xml"]) assert.ok(s.includes(x),x);
});
test("unknown phase has no extraction transports",()=>{
  for(const x of ["wc/store/v1/products","playwright","async_playwright","wp-content/plugins/"]) assert.equal(s.toLowerCase().includes(x.toLowerCase()),false,x);
  assert.match(s,/no_store_api:true/);
  assert.match(s,/no_plugin_extraction:true/);
});
test("strict native acceptance",()=>{
  assert.match(s,/function native\\(body\\)/);
  assert.match(s,/sameHost\\(r\\.final_url,root\\)/);
  assert.ok(s.includes("[\"id\",\"title\",\"link\",\"price\"]"));
});
test("bounded matrix",()=>{
  assert.match(s,/MAX_CANDIDATES = 450/);
  assert.match(s,/const CONCURRENCY = 24/);
  assert.equal(/random.*token.*enumeration/i.test(s),false);
});
