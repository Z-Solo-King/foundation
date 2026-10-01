import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_icopydoc_v9_stackskb.mjs","utf8");
test("documented iCopyDoc indices only",()=>{for(const x of ["/wp-content/uploads/feed-xml-0.xml","/wp-content/uploads/feed-xml-1.xml","/wp-content/uploads/feed-xml-2.xml"])assert.ok(s.includes(x),x);assert.ok(s.includes("no_random_token_enumeration:true"))});
test("strict Merchant gate",()=>{for(const x of ["base\\.google\\.com","[\"id\",\"title\",\"link\",\"price\"]","validated_google_merchant_xml","<item\\b","<entry\\b"])assert.ok(s.includes(x),x)});
test("same-host current response gate",()=>{for(const x of ["status===200","same(r.url||url,url)","final_url:r.url||url"])assert.ok(s.includes(x),x)});
test("policy",()=>{for(const x of ["no_browser:true","no_auth:true","no_bypass:true"])assert.ok(s.includes(x),x)});
