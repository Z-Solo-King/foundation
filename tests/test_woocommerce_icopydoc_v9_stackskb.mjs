import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_icopydoc_v9_stackskb.mjs","utf8");
test("documented iCopyDoc indices only",()=>{for(const x of ["/wp-content/uploads/feed-xml-0.xml","/wp-content/uploads/feed-xml-1.xml","/wp-content/uploads/feed-xml-2.xml"])assert.ok(s.includes(x),x);assert.ok(s.includes("no_random_token_enumeration:true"))});
test("strict Merchant gate",()=>{for(const x of ["base\\.google\\.com","g:id","g:title","g:link","g:price","validated_google_merchant_xml"])assert.ok(s.includes(x),x)});
test("policy",()=>{for(const x of ["no_browser:true","no_auth:true","no_bypass:true"])assert.ok(s.includes(x),x)});
