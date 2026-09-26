# Custom/API Google Merchant XML Feed Recovery — Chat Handoff

Date: 2026-09-26
Repository: `Z-Solo-King/foundation` (public)
Current main: `3b5a2e1c4a8d7b13896b3cbd89a177c06ac17ded`
Audit branch: `feat/foundation-google-feed-matrix-20260926`
Draft PR: #1248 — Google XML feed matrix for custom/API retailers
PR URL: https://github.com/Z-Solo-King/foundation/pull/1248

## Purpose

This handoff is the durable state for the next chat after the current chat reached its limit.

The active objective is to recover **real Google Merchant XML/product feeds** for Indian retailers.

Current scope:
- Include custom/API-style sites.
- Exclude WooCommerce.
- Exclude Shopify.
- Exclude OpenCart.
- Exclude Wix.
- Do not count ordinary product APIs, JSON endpoints, XML sitemaps, RSS without Google Merchant fields, or generic catalog XML as a Google Merchant feed.
- A feed is verified only when the payload itself matches RSS/Atom-style product feed structure and contains the Google namespace/Google product fields with populated product items.
- A 403/429 response means **transport-unverified**, not “no feed”.
- Do not bypass CAPTCHA/Cloudflare challenges, authentication, clearance cookies, or anti-bot controls.

## Source / tooling context

The user supplied `extract_universal_V175.py`, a large universal extraction/mapping tool. It contains platform/feed heuristics and is a useful discovery lens. Relevant existing heuristics include generic merchant/feed paths, Google-feed candidates, sitemap discovery, and host-specific profiles.

Important principle: use V175's knowledge to generate hypotheses, but verify every feed against its actual payload.

## Initial custom/API target set

The 15-site target pool used in the first parallel sweep was:

1. BuildMyPC — https://www.buildmypc.in
2. Clarion Computers — https://shop.clarioncomputers.in
3. CloudTechAsia — https://cloudtechasia.in / https://api.hyperinvento.com
4. DigiBuggy — https://digibuggy.com
5. Easy Shoppi — https://www.easyshoppi.com
6. LebyoPC — https://lebyopc.com
7. Logtech — https://logtech.in
8. Shivam IT Service — https://shivamitservice.com / https://api.shivamitservice.in
9. The Rhythm House — https://www.therhythmhouse.co.in
10. TheValueStore — https://thevaluestore.in
11. altf4gear — https://altf4gear.com
12. ArcadeX — https://www.arcadex.in
13. Fingers — https://www.fingers.co.in
14. KeySync — https://keysync.co / https://api.keysync.co
15. Furtados — https://www.furtadosonline.com

## Execution already completed

Shallow matrix:
- Workflow run: 36242499465
- 15 independent matrix sites
- `fail-fast: false`
- GitHub Actions execution succeeded

Deep source-mining matrix:
- Workflow run: 36242704888
- 14 unresolved sites
- `fail-fast: false`
- Recursive sitemap discovery
- robots.txt discovery
- homepage URL extraction
- JavaScript source URL mining
- alternate API/storefront roots
- GitHub Actions execution succeeded

Temporary probe workflow/scripts were removed from the audit branch after evidence capture. The branch is intended to preserve evidence, not temporary execution machinery.

## VERIFIED GOOGLE MERCHANT XML FEEDS

### 1. Clarion Computers

URL:
https://shop.clarioncomputers.in/feeds/google.xml

Verified:
- HTTP 200
- Payload: 6,754,788 bytes
- 2,152 product items
- Google namespace: http://base.google.com/ns/1.0
- id: 2,152
- title: 2,152
- link: 2,152
- price: 2,152
- availability: 2,152
- condition: 2,152
- brand: 2,152
- gtin: 2,152
- mpn: 2,152
- SHA-256: d96edd0748709b00825456e31ad8bd72d9b5348a2cc1d38d867d4a497053d6c8

### 2. Shivam IT Service

URL:
https://api.shivamitservice.in/google-feed.xml

Verified:
- HTTP 200
- Payload: 2,449,913 bytes
- 1,009 product items
- Google namespace: http://base.google.com/ns/1.0
- id: 1,009
- title: 1,009
- link: 1,009
- price: 1,009
- availability: 1,009
- condition: 1,009
- brand: 1,008
- gtin: 632
- mpn: 982
- SHA-256: f92ad78e0689fb74cb224970ad1d126709703706e501cf630da7a5f73317baae

## CURRENT UNRESOLVED SET

Still unresolved after shallow + deep discovery:

1. BuildMyPC
   - Shallow: 49/49 candidates HTTP 429
   - Deep: 55/55 candidates HTTP 429
   - Treat as transport blocked, not no-feed.

2. Easy Shoppi
   - Shallow: 49/49 candidates HTTP 404
   - Deep: 66 candidates tested; no verified Google XML.

3. Fingers
   - Shallow: 49/49 candidates HTTP 200; no Google XML
   - Deep completed; no verified Google XML.

4. LebyoPC
   - Shallow: 49/49 candidates HTTP 403
   - Deep: 70/70 candidates HTTP 403
   - Treat as transport blocked, not no-feed.

5. ArcadeX
   - Shallow: 49/49 candidates HTTP 404
   - Deep: 58 candidates tested; no verified Google XML.

6. altf4gear
   - Shallow: 35 HTTP 200 + 14 HTTP 404; no Google XML
   - Existing /api/feed is generic JSON, not a Google XML result.

7. Logtech
   - Shallow: 49/49 candidates HTTP 404
   - Existing profile indicates custom Alpine site; no verified public merchant feed.

8. DigiBuggy
   - Shallow: 49/49 HTTP 200; no Google XML
   - DotPe/item API exists but is not itself a Google Merchant XML feed.

9. TheValueStore
   - Shallow: 49/49 HTTP 404
   - Existing /api/x3/products endpoint is catalog JSON, not Google XML.

10. Furtados
    - Shallow: 9 HTTP 200 + 40 HTTP 404; no Google XML
    - GraphQL/catalog paths are not Google Merchant XML.

11. KeySync
    - Shallow: 49/49 HTTP 404
    - Deep: 114 candidates; mixed 200/400/403/404; no verified Google XML.
    - Requires targeted follow-up.

12. The Rhythm House
    - Shallow: 1 HTTP 200 + 48 HTTP 404; no Google XML
    - DotPe item API and sitemap work, but no Google Merchant XML was verified.

13. CloudTechAsia
    - Shallow: 49/49 HTTP 404
    - Deep: 175 candidates tested; no verified Google XML.
    - Uses Hyperinvento API; continue external-feed discovery only.

## Do NOT redo

Do not restart the original 49-path sweep as the primary method.

Do not spend more time on:
- Shopify
- WooCommerce
- OpenCart
- Wix
- ordinary product APIs
- ordinary sitemaps

The next chat should start with the 13-site unresolved set above.

## NEXT EXECUTION PRIORITY

Highest-value next lane:

### Lane A — external/hidden feed discovery
Search for feed URLs that are not same-origin obvious filenames:
- third-party feed-generation services
- external XML hostnames/CDN URLs
- Google Merchant/feed references in HTML, JS, robots, sitemap indexes
- feed URLs embedded in configuration/API responses
- vendor/platform documentation fingerprints
- public GitHub/code references mentioning the retailer feed
- indexed search-engine references to XML feed URLs
- subdomain/API-host feed endpoints

### Lane B — platform-specific source mining
Use known platform clues:
- Hyperinvento / CloudTechAsia
- DotPe / DigiBuggy / Rhythm House
- Vercel-style BuildMyPC
- SvelteKit-style LebyoPC
- GraphQL/Wizzy-style Furtados
- custom Alpine Logtech
- custom JSON/API sites

### Lane C — blocked transport cases
For BuildMyPC and LebyoPC:
- try normal public transport variations only
- alternate public hostnames already exposed by the site
- DNS/public endpoint discovery
- indexed/public references
- GitHub Actions public runner execution
- do not attempt anti-bot bypass.

### Lane D — negative-result strengthening
For accessible sites with no hit:
- inspect all discovered URLs first
- distinguish 404 from soft-404
- distinguish generic XML/RSS from Merchant XML
- validate content type AND payload
- look for external feed-service links before declaring negative.

## GitHub persistence

Canonical evidence file:
`data/feed_lab/custom_api_google_xml_live_evidence_2026-09-26.json`

It contains the two verified feeds and the unresolved set.

The audit work is in draft PR #1248:
https://github.com/Z-Solo-King/foundation/pull/1248

Do not merge temporary audit machinery into main.

## Project / connector separation

This work is GitHub/Foundation-specific.

The project's operating constraint is that GitHub and Cloudflare connector work should be kept in separate chats when connector reliability conflicts. For the next chat, continue the GitHub/Foundation feed work from this handoff. Do Cloudflare-specific operations in the separate Cloudflare chat and share state through the repository/evidence files.

## Handoff instruction for next chat

Start from this document and PR #1248.

First read:
1. this handoff
2. `data/feed_lab/custom_api_google_xml_live_evidence_2026-09-26.json`
3. PR #1248
4. current `main` head
5. the latest extractor/source file if available

Then continue only with the 13 unresolved custom/API retailers.

Target outcome:
**discover additional real Google Merchant XML feed URLs and verify payloads; never count a normal API/sitemap as a feed.**
