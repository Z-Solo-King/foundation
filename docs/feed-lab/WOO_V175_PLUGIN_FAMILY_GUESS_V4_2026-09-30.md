# WooCommerce Plugin-Family XML Guess V4 — 2026-09-30

This lane is the continuation of the completed 30-site plugin extraction/grouping/research work. It does **not** re-run plugin extraction, Store API extraction, sitemap discovery, robots discovery, Playwright, XHR mining, or product capture.

## Input grouping

The manifest is the existing 30-site calibration corpus:

- 10 Phase-1 known-family sites.
- 4 Phase-2 low-confidence family hypotheses.
- 16 remaining unknown-family sites.

For known/hypothesized standalone families, the runner guesses only that family's documented URL grammar. For the 16 unknowns, it runs a bounded cross-family matrix across the documented standalone feed families.

Google for WooCommerce is skipped from standalone XML guessing because its current architecture is API-integrated and does not expose a separate feed URL.

## Research-backed candidate families

- WooCommerce Google Product Feed: query/permalink forms such as `?woocommerce_gpf=google` and `/woocommerce_gpf/google`. citeturn753964search0turn753964search2
- CTX Feed: public query form `?woo_feed=<feed-name>&wt=xml` and feeds commonly stored below `wp-content/uploads/woo-feed/`. citeturn619245search3turn125056search10
- Product Feed Manager/WPPFM: generated feeds are stored under `wp-content/uploads/wppfm-feeds/`. citeturn619245search0
- WebToffee: generated feed filenames/URLs are configurable, so filename guesses are bounded heuristics rather than enumeration.
- CodeSolz Merchant Feed Booster: documented `wp-content/uploads/codesolz-feeds/google-products.xml`. citeturn753964search1
- FeedCraft: documented `/wp-json/feedcraft-product-feed/v1/xml`. citeturn753964search6
- RexFeed: current public support examples show generated XML files under `wp-content/uploads/rex-feed/`, with generated filenames such as `feed-687.xml`. citeturn125056search12

## Acceptance

A hit is accepted only when the current response is same-host and the current payload contains the Google Merchant namespace plus `g:id`, `g:title`, `g:link`, and `g:price` in the same item/entry.

403, 404, 429, timeout, challenge HTML, RSS, sitemap XML, or unrelated XML are recorded as evidence/transport states and never converted into “feed absent”.

## Security boundary

Public GET only. No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, stealth browsing, proxy rotation, random token enumeration, Store API product extraction, or product reconstruction.
