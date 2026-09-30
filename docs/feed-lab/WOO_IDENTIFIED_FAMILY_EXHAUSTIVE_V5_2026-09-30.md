# WooCommerce Identified-Family Exhaustive Guess V5 — 2026-09-30

This phase intentionally covers only the four confirmed standalone feed-generator families. The 16 unknown-family sites and four low-confidence hypotheses are outside this run.

Research changed the guessing strategy:
- WooCommerce Google Product Feed has deterministic query/permalink forms and documented partial-feed parameters. Currency and price-country URL parameters are also documented.
- CTX/WebAppick stores generated feeds under the WooCommerce uploads area, but feed names are configurable; documented/community examples include google_shopping_ctx_1.xml and listings07-style names.
- WPFM uses wp-content/uploads/wppfm-feeds/ and feed names are user-defined; public examples include Google-Products-New.xml and Google-Feed_1.xml.
- AdTribes stores static feed files under woo-product-feed-pro; current docs/examples show random-looking generated names, so random token brute force is not logical. Directory-index and historical public URL recovery are used instead.

The run therefore uses:
1. family-specific deterministic/query grammars;
2. public output-directory XML references where exposed;
3. site-identity semantic filename variants for name-based families;
4. Wayback CDX historical feed URLs, re-probed against the current host;
5. strict current same-host native Merchant XML validation.

A historical URL is only a candidate source. 403/429, challenge pages, 404s, timeouts, sitemaps, RSS and unrelated XML are not positive feeds.

Research:
- WooCommerce GPF query/partial/currency/pricecountry: https://woocommerce.com/document/google-product-feed-feed-generation-options/ and https://woocommerce.com/document/google-product-feed-extension-compatibility/
- WebToffee current feed creation requires a unique file name: https://www.webtoffee.com/docs/product-feed/generate-and-setup-google-product-reviews-feed/
- AdTribes static feed output under woo-product-feed-pro: https://adtribes.io/knowledge-base/cache-plugin-compatibility-with-product-feed-pro/

Repository policy keeps feed workflows public/read-only and separates them from privileged workflows. The workflow uses a four-shard matrix and an aggregate exactly over the four confirmed standalone sites.
