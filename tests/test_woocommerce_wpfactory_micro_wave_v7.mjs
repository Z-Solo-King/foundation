import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_wpfactory_micro_wave_v7.mjs","utf8");
test("target scope",()=>{ for(const x of ["Aarna Computers","Variety Infotech","Theproaudio"]) assert.ok(s.includes(x),x); });
test("deterministic family candidate",()=>{ assert.ok(s.includes("/products.xml")); assert.ok(s.includes("wpfactory_product_xml_feeds")); });
test("guess-only contract",()=>{ assert.ok(s.includes("no_store_api:true")); assert.ok(s.includes("no_plugin_extraction:true")); assert.ok(s.includes("no_browser_automation:true")); });
test("strict native gate",()=>{ assert.ok(s.includes("function native(body)")); assert.ok(s.includes("sameHost(r.url||url,root)")); assert.ok(s.includes("[\"id\",\"title\",\"link\",\"price\"]")); });
test("one-candidate wave",()=>{ assert.ok(s.includes("const CANDIDATE=\"/products.xml\"")); assert.ok(s.includes("candidate_count:1")); });
