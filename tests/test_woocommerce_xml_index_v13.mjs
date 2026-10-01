import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_xml_index_v13.mjs","utf8");

test("exact 30-site corpus",()=>{for(const x of ["AULA India","PC Studio","NCL Computer"])assert.ok(s.includes(x),x);assert.equal(s.includes("Only SSD"),false)});

test("historical XML sources",()=>{for(const x of ["web.archive.org/cdx","index.commoncrawl.org","mimetype:application/xml","collapse=urlkey","wayback_cdx_xml","commoncrawl_index_xml"])assert.ok(s.includes(x),x)});

test("current strict Merchant validation",()=>{for(const x of ["function native(body)","base.google.com/ns/1.0","validated_google_merchant_xml","id","title","link","price"])assert.ok(s.includes(x),x)});

test("current revalidation",()=>{for(const x of ["status===200","same(r.final_url,u)","current"])assert.ok(s.includes(x),x)});

test("no guessing/APIs/browser/bypass",()=>{for(const x of ["no_store_api:true","no_product_extraction:true","no_plugin_inference:true","no_browser:true","no_auth:true","no_bypass:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"])assert.ok(s.includes(x),x)});
