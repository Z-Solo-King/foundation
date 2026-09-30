# WooCommerce Feed Extraction V3 - API First - 2026-09-30

V2 completed its 20-site guessing run, but every target remained unknown-family and the runner spent large budgets on candidate URLs.

V3 changes the execution order:

1. Discover /wp-json/.
2. Inspect registered WordPress REST routes.
3. Query /wp-json/wc/store/v1/products?per_page=100 first.
4. Accept validated public WooCommerce product records as a direct product source.
5. Inspect explicit feed-like REST routes.
6. Probe only a small bounded native XML candidate set.
7. Accept native Google Merchant XML only when the current payload validates.

WooCommerce documents the Store API as public product data with collection pagination up to 100 products per page and X-WP-Total / X-WP-TotalPages headers.

WordPress documents REST API discovery through the /wp-json/ root and registered routes.

The extractor therefore no longer depends on a Google XML file existing for direct WooCommerce product extraction.

Native XML remains a separate transport and is never inferred from sitemap/RSS evidence or guessed filenames alone.

The V3 workflow is six-way sharded, API-first, and bounded for latency and request cost.

Current implementation status: code and unit tests are complete; the PR is waiting on the repository's standard protected PR checks to execute on the latest head.

Security boundary: public requests only. No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication guessing, proxy rotation, rate-limit evasion, or random feed-token enumeration.
