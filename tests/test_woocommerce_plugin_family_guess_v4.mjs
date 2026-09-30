import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const toolPath = path.resolve("tools/woocommerce_plugin_family_guess_v4.mjs");
const source = fs.readFileSync(toolPath,"utf8");

test("uses plugin-family-only guessing contract", () => {
  assert.match(source,/plugin-family-specific-xml-guess-only/);
  assert.doesNotMatch(source,/wc\/store\/v1\/products/);
  assert.doesNotMatch(source,/playwright/i);
  assert.doesNotMatch(source,/add_cookies|seed_cookies|cookie_jars|camoufox|nodriver|curl_cffi/i);
});

test("contains documented family grammars", () => {
  assert.match(source,/woocommerce_gpf=google/);
  assert.match(source,/woo_feed=google/);
  assert.match(source,/wppfm-feeds/);
  assert.match(source,/webtoffee_product_feed/);
  assert.match(source,/codesolz-feeds\/google-products\.xml/);
  assert.match(source,/feedcraft-product-feed\/v1\/xml/);
  assert.match(source,/rex-feed\/feed-687\.xml/);
});

test("native validator requires Google namespace and core fields in one item", () => {
  assert.ok(source.includes("base\\.google\\.com\\/ns\\/1\\.0"));
  assert.ok(source.includes('["id","title","link","price"]'));
  assert.match(source,/<item\\b/);
  assert.match(source,/<entry\\b/);
});

test("same-host validation is explicit", () => {
  assert.match(source,/sameHost\(x\.final_url,site\.root\)/);
  assert.match(source,/sameHost\(finalUrl,url\)/);
});
