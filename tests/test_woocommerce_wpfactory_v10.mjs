import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_wpfactory_v10.mjs","utf8");
test("17 target scope",()=>{for(const x of ["Aarna Computers","Ads Store","EZPZ Solutions","GamesNComps","Variety Infotech"])assert.ok(s.includes(x))});
test("documented WPFactory grammar",()=>{for(const x of ["/products.xml","/products_2.xml","/products_3.xml","/feeds/google.xml"])assert.ok(s.includes(x),x);assert.ok(s.includes("no_random_token_enumeration:true"))});
test("strict native gate",()=>{for(const x of ["base\\.google\\.com","\"id\",\"title\",\"link\",\"price\"","validated_google_merchant_xml","same(x.final_url,root)"])assert.ok(s.includes(x),x)});
test("transport and no-bypass policy",()=>{assert.ok(s.includes("RETRIES=2"));assert.ok(s.includes("RETRY_DELAYS"));for(const x of ["no_store_api:true","no_plugin_extraction:true","no_browser:true","no_auth:true","no_bypass:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"])assert.ok(s.includes(x),x)});
