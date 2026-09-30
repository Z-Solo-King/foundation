import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_google_feed_index_guess_v8.mjs","utf8");
test("unknown cohort remains true unknown",()=>{
  for(const x of ["Aarna Computers","Ads Store","Variety Infotech"]) assert.ok(s.includes(x),x);
  for(const x of ["Kryptronix Gaming","Prime ABGB","NCL Computer"]) assert.equal(s.includes(x),false,x);
});
test("public search-index recovery",()=>{
  for(const x of ["html.duckduckgo.com/html","google.com/search","bing.com/search","parseSearchUrls","search-index"]) assert.ok(s.includes(x),x);
});
test("learned family grammar coverage",()=>{
  for(const x of ["woocommerce_gpf=google","woo_feed=","wppfm-feeds","webtoffee_product_feed","codesolz-feeds","feedcraft-product-feed","rex-feed","klp-feeds-xml","feed-xml-0.xml"]) assert.ok(s.includes(x),x);
});
test("guess-only policy",()=>{
  for(const x of ["no_store_api:true","no_product_extraction:true","no_plugin_extraction:true","no_playwright:true","no_auth:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"]) assert.ok(s.includes(x),x);
});
test("strict native acceptance",()=>{
  assert.ok(s.includes("function native(body)"));
  assert.ok(s.includes("sameHost(r.final_url,root)"));
  assert.ok(s.includes("[\"id\",\"title\",\"link\",\"price\"]"));
});
test("transport bound",()=>{
  assert.match(s,/const TIMEOUT\s*=\s*5000/);
  assert.match(s,/const CONCURRENCY\s*=\s*3/);
  assert.match(s,/slice\(0,500\)/);
});
