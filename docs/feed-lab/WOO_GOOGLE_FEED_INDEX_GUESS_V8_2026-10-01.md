# WooCommerce Google Feed Index Guess V8 — 2026-10-01

This wave continues the unknown-family guessing phase and adds a public-index lane. It does not perform plugin extraction, page crawling, Store API acquisition, browser automation, authentication, or anti-bot bypass.

For each unknown host, V8:
1. runs the learned bounded family URL matrix;
2. queries public search indexes for exact same-host XML/feed URLs using site-restricted queries;
3. accepts only candidate URLs that are current same-host Google Merchant XML payloads;
4. records blocked/transport-limited responses separately.

The search queries target filetype XML, Google Merchant namespace text, and merchant/product feed references. Historical/search-engine hits are candidate sources only; they are never accepted without current validation.

Six shards cover the 17 unknown targets.