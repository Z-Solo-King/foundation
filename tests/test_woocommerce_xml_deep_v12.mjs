import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_xml_deep_v12.mjs","utf8");
test("exact 30-site corpus",()=>{for(const x of ["AULA India","Only SSD"])assert.equal(s.includes(x),x==="Only SSD"?false:true);for(const x of ["PC Studio","Aarna Computers","NCL Computer"])assert.ok(s.includes(x),x)});
test("XML-only discovery",()=>{for(const x of ["filetype:xml","base.google.com/ns/1.0","g:id","g:price","feed-xml","wayback_exact_xml","current_homepage"])assert.ok(s.includes(x),x)});
test("strict native gate",()=>{for(const x of ["function native(body)","same(r.final_url,root)","validated_google_merchant_xml","http://base.google.com/ns/1.0","https://base.google.com/ns/1.0"])assert.ok(s.includes(x),x)});
test("no API/browser/bypass",()=>{for(const x of ["no_store_api:true","no_product_extraction:true","no_plugin_inference:true","no_browser:true","no_auth:true","no_bypass:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"])assert.ok(s.includes(x),x)});
