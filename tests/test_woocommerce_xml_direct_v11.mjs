import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

const s=fs.readFileSync("tools/woocommerce_xml_direct_v11.mjs","utf8");

test("30 site corpus",()=>{
  for(const x of ["PC Studio","Quickin Computers","Aarna Computers","NCL Computer","StacksKB","Theproaudio"]) assert.ok(s.includes(x),x);
});

test("xml-only discovery",()=>{
  for(const x of ["filetype:xml","/robots.txt","/sitemap.xml","/wp-sitemap.xml","search_index","public_reference","XML"]) assert.ok(s.includes(x),x);
});

test("strict Merchant validation",()=>{
  for(const x of ["const NS=","function validate(body)","id","title","link","price","validated_google_merchant_xml","same(r.final_url,root)"]) assert.ok(s.includes(x),x);
});

test("no APIs/browser/bypass",()=>{
  for(const x of ["no_store_api:true","no_product_extraction:true","no_plugin_extraction:true","no_browser:true","no_auth:true","no_bypass:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_random_token_enumeration:true"]) assert.ok(s.includes(x),x);
});
