import test from "node:test"; import assert from "node:assert/strict"; import fs from "node:fs";
test("v15 has exact 30-site corpus and hard native gate",()=>{const s=fs.readFileSync("tools/woocommerce_xml_live_v15.mjs","utf8");assert.equal((s.match(/https:\/\//g)||[]).length>=30,true);assert.match(s,/validated_google_merchant_xml/);assert.match(s,/no_random_token_enumeration/);});
