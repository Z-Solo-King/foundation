# WooCommerce Feed Extraction V3 - API First - 2026-09-30

V2 completed its 20-site guessing run, but it spent large budgets on candidate URLs while every target still remained unknown-family.

V3 changes the execution order:

1. Discover /wp-json/.
2. Inspect the WordPress REST API routes and namespaces.
3. Query the public WooCommerce Store API products endpoint with per_page=100.
4. Accept that response as a direct WooCommerce product source when product records validate.
5. Probe only explicit feed-like REST routes plus a small bounded XML set.
6. Accept native Google Merchant XML only when the current payload validates.

WooCommerce documents public product data through the Store API and collection pagination up to 100 products per page, with X-WP-Total and X-WP-TotalPages headers.

WordPress documents that the REST API root exposes namespaces and registered routes, allowing capability discovery without authentication.

The V3 design therefore does not require a Google XML file to extract public WooCommerce product data.

Native XML remains a separate transport. It is never inferred from sitemap/RSS data or a guessed filename alone.

The workflow is six-way sharded, API-first, and intentionally bounded for runtime and request cost.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication guessing, proxy rotation, rate-limit evasion, or random feed-token enumeration is used.
