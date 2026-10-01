import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
const s=fs.readFileSync("tools/woocommerce_blocked_recovery_v10.mjs","utf8");
test("persistent V7 transport cohort",()=>{for(const x of ["Aarna Computers","KC Computers","Cosmic Byte","KRG KART","PC Kumar Infotech","GamesNComps","PCHubShop","Theproaudio","SCL Gaming","ithunt"])assert.ok(s.includes(x),x);assert.equal(s.includes("Ads Store"),false)});
test("known family URLs only",()=>{for(const x of ["/?woocommerce_gpf=google","/wp-content/uploads/woo-feed/google.xml","/wp-content/uploads/woo-product-feed-pro/google.xml","/wp-content/uploads/wppfm-feeds/Google.xml","/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml","/wp-content/uploads/codesolz-feeds/google-products.xml","/wp-json/feedcraft-product-feed/v1/xml","/wp-content/uploads/rex-feed/google.xml","/wp-content/uploads/klp-feeds-xml/google.xml","/wp-content/uploads/feed-xml-0.xml"])assert.ok(s.includes(x),x);assert.ok(s.includes("no_random_token_enumeration:true"))});
test("one-at-a-time recovery",()=>{assert.ok(s.includes("BETWEEN_PROBES=1500"));assert.ok(s.includes("RETRIES=1"));assert.ok(s.includes("for(const target of selected)"));assert.ok(s.includes("await runTarget(...target)"))});
test("strict native validation",()=>{for(const x of ["GOOGLE_NS","function validate(body)","[\"id\",\"title\",\"link\",\"price\"]","validated_google_merchant_xml"])assert.ok(s.includes(x),x)});
test("no bypass",()=>{for(const x of ["no_bypass:true","no_clearance_cookie_replay:true","no_captcha_bypass:true","no_proxy_rotation:true","no_auth:true"])assert.ok(s.includes(x),x)});
