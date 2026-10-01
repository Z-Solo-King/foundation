# WooCommerce Google XML Feed Recovery — Cross-Chat Handoff Checkpoint
Date: 2026-10-01 (Asia/Kolkata)

## 0. Purpose

This document is the durable handoff for the WooCommerce Google Merchant XML feed guessing work.

The required pipeline is:

1. Existing product extraction / plugin-fingerprint work is considered prior work.
2. Group sites by observed plugin/feed-family fingerprint.
3. Research the feed URL grammar for each family.
4. Guess and probe the family-specific Google XML/feed URLs.
5. Only then move unresolved sites into the unknown-family cross-family guessing stage.
6. Never count a generic API, sitemap, RSS/Atom feed, Store API JSON response, historical-only URL, or reconstructed XML as a native Google Merchant feed.

This checkpoint intentionally preserves that order.

---

## 1. Canonical repository

Repository: Z-Solo-King/foundation
Main currently contains the merged identified-family work and the merged unknown-family V6 guess-only work.

Recent merge receipts:

### PR #1632 — initial plugin-family guessing V4
Merged into main.
Purpose: 30-site plugin-family guessing corpus.
Run: 36749419144
Aggregate artifact: 11113389753
Result: 30/30 executed; 0 native Google Merchant XML verified.
Important classification:
- 7 Google-for-WooCommerce / API-integrated families skipped for standalone XML guessing.
- 8 clean no-hit sites.
- 15 transport-limited.
- 1,711 bounded URL hypotheses.
This was the completion of the original 30-site guessing wave.

### PR #1640 — identified standalone family expansion
Merged into main.
Merge commit: 8ecbb1fb408978393f3c83e56c3384b23c64b512
Run: 36759700843
Aggregate artifact: 11118179102
Purpose: exhaust every standalone family that the V4 grouping/research evidence had already identified.

Seven identified standalone targets were explicitly covered:
- PC Studio → WooCommerce Google Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Quickin Computers → CTX Feed / WebAppick
- Avikaretails → AdTribes Product Feed PRO
- IT Gadgets Online → Product Feed Manager / WPFM
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed

The run completed successfully and verified 0 native Google Merchant XML feeds.
Interpretation:
- 2 clean no-hit targets: IT Gadgets Online, Kryptronix Gaming.
- 5 transport-limited targets.
- No plugin extraction or Store API extraction was added.

### PR #1645 — true unknown-family V6
Merged into main.
Merged at 2026-09-30T19:06:30Z.
Merge commit reported by GitHub: 64444f0d099b6846fc79acd3b293758ee6a84aab.
Final head SHA before merge: cff6524041fae5d78bb5ef7f992a8bba3eab4531.

Run: 36762779827
Six shards succeeded + aggregate succeeded.
Aggregate artifact: 11119362182.

V6 true-unknown scope:
Aarna Computers
Ads Store
EZPZ Solutions
GamesNComps
hotshiftpc
ithunt
KC Computers
KRG KART
PC Kumar Infotech
PCHubShop
SCL Gaming
Viper PC
Cosmic Byte
Meckeys
StacksKB
Theproaudio
Variety Infotech

Variety Infotech was intentionally returned to the unknown group because the earlier Google-for-WooCommerce hypothesis lacked current public plugin evidence.

V6 execution:
- 17 unique targets.
- 7,468 candidate URL hypotheses.
- 0 native Google Merchant XML feeds verified.
- 17/17 classified as transport-limited.
- 0 clean negatives.

This result is NOT proof that these 17 sites do not publish a feed. The transport-heavy result means the next wave must reduce burst/rate effects and use adaptive public probing.

Representative transport results from V6:
- Aarna: 21 HTTP 200, 429 timeouts.
- Ads Store: 258 HTTP 403/challenges + 192 timeouts.
- GamesNComps: 17 HTTP 200, 113 HTTP 403, 265 HTTP 404, 29 timeouts, 378 challenge markers.
- hotshiftpc: 25 HTTP 200, 208 HTTP 403, 15 HTTP 404, 167 timeouts.
- ithunt: 424 HTTP 403/challenges.
- KC Computers: 450 HTTP 403.
- KRG KART: 401 HTTP 403/challenge, 40 HTTP 404, 9 timeouts.
- PC Kumar Infotech: 450 HTTP 403/challenge.
- SCL Gaming: 49 HTTP 403, 197 HTTP 404, 204 timeouts.
- StacksKB: 6 HTTP 200, 3 HTTP 404, 415 timeouts.
- Variety Infotech: 5 HTTP 200, 116 HTTP 403/challenge, 329 timeouts.
- Viper PC: 23 HTTP 200, 258 HTTP 403, 169 timeouts.
- EZPZ Solutions: 379 HTTP 200, 7 HTTP 404, 64 timeouts.
- Meckeys: 83 HTTP 404, 341 timeouts.
- PCHubShop: 104 HTTP 403, 82 HTTP 404, 238 timeouts, 186 challenge markers.
- Cosmic Byte: 443 HTTP 403/challenge, 7 HTTP 404.
- Theproaudio: 424 HTTP 403/challenge.

The key lesson from V6:
24-way per-target concurrency is too aggressive for this corpus and turns otherwise reachable sites into timeouts/challenge-heavy observations. Do not use V6's transport status as plugin-family evidence.

---

## 2. Research-backed feed-family grammar learned so far

Families already researched and encoded in the guessers:

1. WooCommerce Google Product Feed
   - documented endpoint/query shape including:
     /?woocommerce_gpf=google
     /woocommerce_gpf/google
   - partial-feed parameters:
     gpf_start
     gpf_limit
   - currency / price-country parameters are known URL modifiers.

2. CTX Feed / WebAppick
   - public output area commonly under:
     /wp-content/uploads/woo-feed/
   - documented/community names include:
     google_shopping_ctx_1.xml
     google_shopping_ctx_1-3.xml
     listings07.xml
     merchantcenter2.xml
   - query grammar includes:
     ?woo_feed=<feed>&wt=xml

3. Product Feed Manager / WPFM
   - output area:
     /wp-content/uploads/wppfm-feeds/
   - user-defined filenames are expected.
   - researched examples include:
     Google-Products-New.xml
     Google-Feed_1.xml

4. AdTribes Product Feed PRO
   - output area:
     /wp-content/uploads/woo-product-feed-pro/
     /wp-content/uploads/woo-product-feed-pro/xml/
   - generated filenames can be random-looking, so DO NOT brute-force random IDs/tokens.
   - directory/index and historical-public-reference recovery are the rational paths.

5. WebToffee Product Feed
   - output area:
     /wp-content/uploads/webtoffee_product_feed/
   - user-configurable filename shapes.
   - researched examples include:
     wt_google_Feed.xml
     wt_gs_Feed.xml
     wt_gmc_Feed.xml
     wt_google_products_Feed.xml

6. CodeSolz Merchant Feed Booster
   - known public output path family:
     /wp-content/uploads/codesolz-feeds/
   - canonical researched example:
     google-products.xml

7. FeedCraft
   - researched REST-style family:
     /wp-json/feedcraft-product-feed/v1/xml

8. RexFeed
   - output area:
     /wp-content/uploads/rex-feed/
   - public examples include generated feed-<id>.xml style names.
   - random ID enumeration is not an acceptable strategy.

9. KLPSoft
   - output area:
     /wp-content/uploads/klp-feeds-xml/

10. iCopyDoc
    - researched public feed files include:
      /wp-content/uploads/feed-xml-0.xml
      and related feed XML naming patterns.

Google-for-WooCommerce / Google Listings & Ads:
- This is an API-integrated architecture, not a simple native XML filename family.
- These sites are not supposed to be forced into standalone XML URL guessing.

---

## 3. Strict native feed acceptance

A URL counts as a native Google Merchant feed only when the CURRENT response:

- is publicly reachable;
- returns HTTP 200;
- remains on the same host after redirects;
- is XML/RSS/Atom-like;
- is not a CAPTCHA/Cloudflare/access-denied page;
- contains Google Merchant namespace:
  https://base.google.com/ns/1.0
- contains, within the same <item> or <entry>:
  g:id
  g:title
  g:link
  g:price

Never count:
- sitemap XML;
- WordPress /feed/ or comments feed;
- Store API JSON;
- generic product/category APIs;
- GraphQL;
- historical-only URLs;
- guessed URL existence without Merchant XML payload validation;
- reconstructed/converted XML.

Transport states:
- 403
- 429
- timeout
- challenge/access-denied
must remain transport-unverified, NOT “feed absent”.

---

## 4. What NOT to repeat

Do not restart:
- WooCommerce Store API extraction.
- Generic product extraction.
- Plugin extraction/fingerprinting for the already grouped cohort.
- Broad HTML/robots/sitemap crawling for these tasks.
- Playwright/XHR discovery as a substitute for this guessing phase.
- Blind huge filename matrices without a family rationale.
- Random 32-character/token/ID enumeration for generated-feed families.
- CAPTCHA/Cloudflare bypass.
- clearance-cookie replay.
- authentication bypass.
- proxy rotation/evasion.

V4 and V6 already established these boundaries.

---

## 5. Exact continuation strategy

### V7 — transport-aware unknown-family guessing

Objective:
Convert the 17/17 V6 transport-limited result into useful family evidence without increasing extraction scope.

Per target:
1. Start with one request per family, not a 20–24 request burst.
2. Family probe order:
   - WooCommerce GPF core endpoint.
   - CTX/WebAppick canonical directory/query.
   - WPFM directory.
   - WebToffee directory.
   - AdTribes directory.
   - CodeSolz canonical filename.
   - FeedCraft REST endpoint.
   - RexFeed directory.
   - KLPSoft directory.
   - iCopyDoc canonical file.
   - small generic XML paths.
3. Use low concurrency, ideally 1–3 requests per host.
4. Record transport separately from semantic response.
5. If a family returns a stable HTTP 200 response, expand ONLY that family grammar for the target.
6. If 403/429/timeouts happen, back off and retry one-at-a-time; do not fan out.
7. A 200 response is still not a positive feed until strict Merchant XML validation succeeds.
8. Store family-level evidence scores such as:
   - response reachability;
   - repeated 200 consistency;
   - family-specific path success;
   - XML shape;
   - Merchant namespace;
   - core-field presence;
   - transport stability.

The output should identify:
- feed verified;
- likely family / strong family evidence;
- unknown but reachable;
- transport blocked.

Do not turn “likely family” into final identity without corroboration.

### V8 — plugin-family identification from already-collected public evidence

Only for sites where V7 produces stable public 200s:
- use existing extraction/fingerprint artifacts already in the repository;
- compare known URL namespaces, public script/source references, headers and response paths;
- map observed signatures to the researched family catalog above;
- then run that family's narrow URL grammar.

This is identification/reuse of prior evidence, not a new broad extraction pipeline.

### V9 — second unknown grammar expansion

Only after V7/V8:
- expand filenames based on actual site/family evidence;
- include site-name variants only where user-configurable filenames make sense;
- include historical public references;
- do NOT create random token enumerators.

### V10 — blocked-target recovery

For persistent 403/429/timeout sites:
- one-at-a-time public requests;
- spaced retries;
- use already-known feed-family URLs;
- preserve transport-unverified state.
No bypass.

---

## 6. Recommended parallel lane layout for the next chat

Use six shards, but reduce per-host concurrency.

Lane 1:
Aarna, Ads Store, EZPZ

Lane 2:
GamesNComps, hotshiftpc, ithunt

Lane 3:
KC Computers, KRG KART, PC Kumar Infotech

Lane 4:
PCHubShop, SCL Gaming, Viper PC

Lane 5:
Cosmic Byte, Meckeys, StacksKB

Lane 6:
Theproaudio, Variety Infotech

Each lane must remain 100% independent in target coverage and emit one durable JSON result per target.

---

## 7. Current code state

Merged/current tools:
- tools/woocommerce_plugin_family_guess_v4.mjs
- tools/woocommerce_identified_family_guess_v5.mjs
- tools/woocommerce_unknown_family_guess_v6.mjs

Merged workflow:
- .github/workflows/woocommerce-identified-family-exhaustive-v5.yml
- .github/workflows/woocommerce-unknown-family-guess-v6.yml

V7 branch was started but no V7 implementation was completed before this chat reached its limit:
- branch: feat/wc-unknown-family-guess-v7-20261001
- it should be treated as an unfinished staging branch, not authoritative.

Use current main as the source of truth, not any abandoned branch.

---

## 8. Current canonical issue state

WooCommerce issue:
#1247 — feed: WooCommerce Google Feed Recovery — 21 active unresolved targets

Custom/API sibling:
#1249 — feed: Custom/API Google Feed Recovery — chat handoff

Important #1249 comment:
- 5916114629 records the final V4 30-site plugin-family guessing completion.
- Earlier comments establish that 403/429/challenge are transport-unverified and that the broad filename sweep should not be repeated.

The next chat should add a new synchronization comment to #1247 and #1249 after each material V7/V8 run.

---

## 9. Goal for the next chat

Do not interpret “0 verified feeds” as success.

The operational goal is:
1. identify every remaining plugin/feed family where evidence supports it;
2. get a real current public Google Merchant XML URL wherever one exists and is publicly accessible;
3. separate transport blockers from genuine negative URL evidence;
4. keep learning the family grammar from every confirmed result;
5. only stop a target after its evidence reaches a defensible terminal state.

The next chat should begin by reading this checkpoint from main, checking #1247/#1249 comments, checking any V7 branch state, then running V7 transport-aware family probes.



---

## 10. V7 completed — 2026-10-01

The adaptive V7 implementation is now the authoritative unknown-family runner. It uses six independent shards, 17 true-unknown targets, one representative endpoint per researched family, low concurrency, slow retries for 403/429/timeouts, transport/semantic separation, and strict Merchant XML validation. V7 explicitly does not restart Store API/plugin extraction or use browser/XHR discovery as its primary method. fileciteturn88file5L1-L1

Live run: 36820461029.

Result:
- 17/17 targets completed.
- 0 native Google Merchant XML feeds verified.
- 10 transport-limited.
- 7 clean/no-hit.
- StacksKB produced the only useful family signal: /wp-content/uploads/feed-xml-0.xml returned current HTTP 200 application/xml but an empty payload.

Transport-limited remains transport-unverified, not feed absence.

## 11. V8/V9 targeted recovery — StacksKB / iCopyDoc

V8 independently corroborated the iCopyDoc URL grammar from published iCopyDoc documentation. The current StacksKB endpoint matched that grammar, but plugin identity was not promoted without corroborating current evidence.

V9 live run: 36820858331.

Current public results:
- /wp-content/uploads/feed-xml-0.xml -> HTTP 200, same host, application/xml, empty payload.
- /wp-content/uploads/feed-xml-1.xml -> HTTP 404.
- /wp-content/uploads/feed-xml-2.xml -> HTTP 404.
- 0 native Merchant XML feeds verified.

This targeted hypothesis is terminal for the currently documented iCopyDoc public indices. It does not prove plugin absence and must not expand into arbitrary index/token enumeration.

## 12. V10 documented WPFactory family recovery

Current main at the canonical branch update is e9b67e37c997e7c51a5a20fb158930727302b120. The known WPFactory family was tested because repository research identifies /products.xml as its deterministic default feed path. citeturn954034search0turn954034search1

Live run: 36821812408.

Result:
- 17/17 targets completed.
- 0 native Google Merchant XML feeds verified.
- 0 WPFactory family signals.
- 9 transport-limited.
- 8 clean 404/non-XML outcomes.
- No target reached the stable non-empty XML expansion gate, so no additional WPFactory paths were probed.

The WPFactory family path therefore remains unverified for this cohort rather than “absent”.

## 13. Current completion boundary

The repository now preserves V7 adaptive recovery, V8 family identification, V9 deterministic family expansion, and V10 WPFactory family testing as auditable stages.

No current native Google Merchant XML URL has been recovered for the 17 true-unknown targets.

The unresolved targets remain divided into evidence categories: current clean negatives for tested deterministic paths, family hypotheses that terminate without a populated feed, and persistent transport-limited sites that remain unverified.

Do not claim global feed absence or final recovery completion from these results alone. Future work should start from new public/current evidence or a newly discovered family grammar, not from another blind filename matrix.


## 14. V10B persistent blocked-target recovery — 2026-10-01

Run: 36822925864.

The ten V7 transport-limited targets were retried one-at-a-time through the ten already-researched family representative URLs, with slow retry and inter-probe spacing.

Result:
- 0/10 current native Google Merchant XML feeds verified.
- 2/10 changed from the earlier transport state to public reachability without producing a native feed: Aarna Computers and GamesNComps.
- 8/10 remain transport-limited: Cosmic Byte, ithunt, KC Computers, KRG KART, PC Kumar Infotech, PCHubShop, SCL Gaming, Theproaudio.
- Aarna returned 9 HTTP 200 responses, but the family URLs resolved to ordinary HTML/category content; no useful family-specific feed signal.
- GamesNComps returned one 200 ordinary HTML response for the WooCommerce GPF query and 404s/blocked responses for the remaining family URLs; no native feed or family signal.
- No target generated a new family-specific expansion gate.

Interpretation: the slower recovery materially reduced false transport conclusions for two targets, but did not recover a current native Merchant XML feed. The eight persistent blockers remain unverified rather than negative.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, proxy rotation/evasion, random token enumeration, Store API extraction, plugin extraction, or browser/XHR discovery was used.

### Current completion boundary after V10B

All ten previously researched family representatives have now been exercised against the persistent blocked cohort under a slow public-only transport strategy. Further work requires genuinely new public/current evidence or a newly corroborated feed-family grammar. Do not restart a blind cross-family matrix merely because native hits remain zero.


## 15. V19 non-empty recovery engineering — 2026-10-02

The prior `wc-google-feed-latest` publication was audited before continuation. It contained 30 XML assets, but 27 were empty XML shells; file existence therefore was not accepted as feed completion.

V19 adds a dedicated six-shard production recovery pipeline. It keeps native Google Merchant XML certification strict, while generating explicitly labeled synthetic public-catalog XML when native XML is unavailable. The builder now uses 12-second fast and 60-second slow public probes, WooCommerce Store API, Shopify `products.json`, WordPress product REST, homepage JSON-LD/microdata, sitemap/robots discovery, live product pages, and Common Crawl as a last-resort public archive source.

Operations builder commit: `fdfa366f1c32347dc43e72ddf607831cb0d9abb8`.
Native rescue timeout repair: `4f026663e196bacd9b9951d5f79b48a4c93c3974`.
Foundation V19 workflow: PR #1814.

The V19 publisher has a hard 30/30 non-empty gate; it refuses to publish empty XML shells. The legacy V18 automatic publisher is retired from automatic execution so it cannot overwrite the V19 publication with weaker output.

Native-feed evidence remains separate from synthetic/archive-backed output. No CAPTCHA solving, Cloudflare clearance replay, authentication bypass, proxy evasion, or fabricated product values are permitted.
