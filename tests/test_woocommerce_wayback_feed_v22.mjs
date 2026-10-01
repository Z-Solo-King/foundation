import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
test("wayback v22 contract",()=>{
 const s=fs.readFileSync("tools/woocommerce_wayback_feed_v22.mjs","utf8");
 assert.match(s,/collapse=urlkey/);
 assert.match(s,/random_filename_generation:false/);
 assert.match(s,/validated_google_merchant_xml/);
 assert.match(s,/const targets=\[/);
 const section=s.slice(s.indexOf("const targets=["),s.indexOf("];",s.indexOf("const targets=["))+2);
 assert.equal((section.match(/\["[^"]+","[^"]+"\]/g)||[]).length,30);
});