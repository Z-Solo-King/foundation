import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const source=fs.readFileSync(path.resolve("tools/woocommerce_plugin_family_guess_v4.mjs"),"utf8");

test("wave 2 is still guessing only",()=>{
  assert.match(source,/plugin-family-specific-xml-guess-only/);
  assert.doesNotMatch(source,/wc\/store\/v1\/products/);
  assert.doesNotMatch(source,/playwright/i);
  assert.doesNotMatch(source,/add_cookies|seed_cookies|cookie_jars|camoufox|nodriver|curl_cffi/i);
});

test("wave 2 contains researched grammar expansions",()=>{
  for(const s of ["listings07.xml","google_shopping_ctx_1.xml","Google-Products-New.xml","wt_fb_Feed.xml","feed-15364.xml","klp-feeds-xml","feed-xml-0.xml"]) {
    assert.ok(source.includes(s), s);
  }
});

test("native validator remains strict",()=>{
  assert.match(source,/base.*google.*ns.*1\.0/s);
  assert.match(source,/\["id","title","link","price"\]/);
});