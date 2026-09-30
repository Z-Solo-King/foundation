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
test("guess-only policy contract",()=>{
  for(const x of ["no_store_api:true","no_product_extraction:true","no_plugin_extraction:true","no_playwright:true","no_auth:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"]) assert.ok(s.includes(x),x);
});
test("strict native acceptance",()=>{
  assert.ok(s.includes("function native(body)"));
  assert.ok(s.includes("sameHost(r.final_url,root)"));
  assert.ok(s.includes("[\"id\",\"title\",\"link\",\"price\"]"));
});
test("bounded matrix",()=>{
  assert.ok(s.includes("MAX_CANDIDATES = 450"));
  assert.ok(s.includes("const CONCURRENCY = 24"));
});
