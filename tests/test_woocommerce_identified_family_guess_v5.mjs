import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_identified_family_guess_v5.mjs","utf8");
test("confirmed standalone scope only",()=>{assert.match(s,/confirmed-standalone-only/);assert.doesNotMatch(s,/unknown20|unknown_woocommerce/)});
test("researched families",()=>{for(const x of ["woocommerce_gpf=google","woo_feed=google","woo-feed/google/xml","woo-product-feed-pro/xml","wppfm-feeds","Google-Products-New.xml","google_shopping_ctx_1.xml","listings07.xml","merchantcenter2.xml"])assert.ok(s.includes(x),x)});
test("wayback + directory recovery",()=>{assert.match(s,/web\.archive\.org\/cdx\/search\/cdx/);assert.match(s,/current-directory-index/);assert.match(s,/wayback-reference/)});
test("no random token enumeration",()=>{assert.doesNotMatch(s,/32.?character.?random/);assert.doesNotMatch(s,/random.?token.?enumerat/)});
test("strict native gate",()=>{assert.match(s,/function native\(body\)/);assert.match(s,/sameHost\(r\.final_url,site\.root\)/);assert.ok(s.includes('["id","title","link","price"]'))});
