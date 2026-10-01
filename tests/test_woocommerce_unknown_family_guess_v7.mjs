import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_unknown_family_guess_v7.mjs","utf8");
test("17-target unknown scope",()=>{for(const x of ["Aarna Computers","Ads Store","Variety Infotech"])assert.ok(s.includes(x));for(const x of ["Kryptronix Gaming","Prime ABGB","NCL Computer"])assert.equal(s.includes(x),false,x)});
test("all researched families have representatives",()=>{for(const x of ["woocommerce_google_product_feed","ctx_feed_webappick","adtribes_product_feed_pro","wpfm_product_feed_manager","webtoffee_product_feed","codesolz_merchant_feed_booster","feedcraft","rexfeed","klpsoft","icopydoc"])assert.ok(s.includes(x),x);assert.equal((s.match(/representative:/g)||[]).length,10)});
test("strict native acceptance",()=>{for(const x of ["base\\.google\\.com","g:id","g:title","g:link","g:price","sameHost(last.final_url,url)"])assert.ok(s.includes(x),x)});
test("transport retry and low concurrency",()=>{assert.ok(s.includes("RETRIES=2"));assert.ok(s.includes("RETRY_DELAYS"));assert.ok(s.includes("CONCURRENCY=2"));assert.ok(s.includes("last.status===403||last.status===429||last.transport==="timeout""))});
test("policy contract",()=>{for(const x of ["no_store_api:true","no_plugin_extraction:true","no_browser:true","no_auth:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"])assert.ok(s.includes(x),x)});
