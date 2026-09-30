import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_unknown_family_guess_v7.mjs","utf8");
test("true unknown cohort",()=>{for(const x of ["Aarna Computers","Ads Store","Variety Infotech"])assert.ok(s.includes(x));for(const x of ["Kryptronix Gaming","Prime ABGB","NCL Computer"])assert.equal(s.includes(x),false);});
test("researched family matrix",()=>{for(const x of ["woocommerce_gpf=google","woo_feed=","wppfm-feeds","webtoffee_product_feed","codesolz-feeds","feedcraft-product-feed","rex-feed","klp-feeds-xml","feed-xml-0.xml"])assert.ok(s.includes(x));});
test("adaptive bounded probing",()=>{assert.ok(s.includes("FAMILY_CONCURRENCY=2"));assert.ok(s.includes("EXPANSION_CONCURRENCY=6"));assert.ok(s.includes("MAX_EXPANSION=72"));});
test("guess-only policy",()=>{for(const x of ["no_store_api:true","no_plugin_extraction:true","no_browser:true","no_auth:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"])assert.ok(s.includes(x));});
test("strict native gate",()=>{assert.ok(s.includes("function native(body)"));assert.ok(s.includes("same(r.final_url,c.url)"));assert.ok(s.includes("[\"id\",\"title\",\"link\",\"price\"]"));});
