# WooCommerce High-Confidence Feed Calibration Learning — 2026-09-30

## Phase 1 result

Targets:
- PC Studio — WooCommerce Google Product Feed
- Quickin Computers — CTX Feed / WebAppick
- Avikaretails — Product Feed PRO / AdTribes
- IT Gadgets Online — Product Feed Manager / WPPFM

Phase 1 fixed-path + filename guessing result: **0/4 native Google Merchant XML feeds verified**.

## Observed response patterns

### PC Studio / WooCommerce Google Product Feed
- `/?woocommerce_gpf=google` returned HTTP 403 with an access-denied/interstitial response.
- Some partial-feed query variants returned HTTP 200 but were full HTML, not XML.
- The permalink-style `/woocommerce_gpf/google` route returned HTTP 404.
- Generic root XML guesses were predominantly 404 or challenge responses.

Learning:
- Do not infer that the official plugin is absent from a 403/HTML response.
- For this family, query-vs-permalink behavior must be recorded separately.
- Public plugin configuration references and browser/network discovery are higher-value than generic filename guessing.

### Quickin Computers / CTX Feed
- Public references included ordinary `/feed/` and sitemap URLs, which must not be promoted as Merchant feeds.
- CTX query hypotheses returned HTTP 200 HTML rather than native Merchant XML.
- The plugin's generated filenames remain unresolved.

Learning:
- CTX filenames are merchant-selected; public directory indexing and exact feed references are primary.
- Generic `feed/` results are normal WordPress RSS and should be excluded automatically.
- Browser resource/XHR inspection is needed to locate hidden feed-generation references.

### Avikaretails / Product Feed PRO
- Public sitemap/product-sitemap surfaces were live but contained no Google namespace.
- The known upload-folder filename hypotheses were not verified.
- Product Feed PRO is documented to use static generated files and may expose non-deterministic filenames.

Learning:
- Arbitrary filename enumeration is low-yield for Product Feed PRO.
- Directory indexes, HTML/source references, historical feed URLs, and feed-list traces should rank above guessed names.
- Current payload validation is mandatory.

### IT Gadgets Online / WPFM
- Public sitemap surfaces were accessible and clearly non-Merchant XML.
- Fixed filenames under `/wp-content/uploads/wppfm-feeds/` returned 404 HTML.
- No native payload was verified.

Learning:
- WPFM feed filenames are merchant-defined rather than guaranteed to be `google.xml`.
- The feed directory itself is a better discovery primitive than expanding generic names.

## Phase 2 improved method

The next calibration run therefore uses:
1. Clean Chromium + Firefox + WebKit discovery.
2. Same-host request/XHR/resource capture.
3. Public WordPress REST namespaces.
4. Public robots/sitemap discovery.
5. Public output-directory discovery.
6. Wayback feed-like URL hints followed by current validation.
7. Plugin-specific candidates before generic fallbacks.
8. Up to 80 direct feed probes for the four high-confidence targets.
9. Strict current Google Merchant validation; no challenge bypass or cookie replay.

## Reuse rules for the unknown 20

The unknown-family cohort should inherit evidence only after it is observed:
- If a public directory exposes generated XML, learn the directory + filename structure.
- If a public HTML/XHR reference exposes a feed, learn the URL grammar.
- If a plugin family is positively fingerprinted, switch that site into the matching learned family lane.
- Do not classify a site from a generic WooCommerce stack alone.
- Do not turn HTTP 403, 429, challenge pages, 404 HTML, sitemaps, or historical-only URLs into feed absence.

The key learning objective is **pattern transfer from verified/public evidence**, not increasing the number of blind filename permutations.
