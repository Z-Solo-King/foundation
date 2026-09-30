import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_svmpforge_historical_v8.mjs","utf8");
test("svmpforge scope",()=>{assert.ok(s.includes("svmpforge_product_feed"));assert.ok(s.includes("/apfw-feed/*.xml"));assert.equal(/random.?token.?enumerat/i.test(s),false);});
test("current re-probe",()=>{assert.ok(s.includes("web.archive.org/cdx/search/cdx"));assert.ok(s.includes("native(body)"));assert.ok(s.includes("same(r.final_url,root)"));});
test("unknown sites only",()=>{for(const x of ["Prime ABGB","Kryptronix Gaming","NCL Computer"])assert.equal(s.includes(x),false);});
