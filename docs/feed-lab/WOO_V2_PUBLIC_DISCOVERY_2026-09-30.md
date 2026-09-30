# WooCommerce Feed Guessing V2 — Public Discovery — 2026-09-30

## Why V2 exists

The previous unknown-20 guessing run completed successfully but produced 20/20 unknown-family results and 0 native-feed hits. The execution pipeline was healthy, but the learning stage had two concrete weaknesses:

1. calibration candidate transfer did not require expected-family/detected-family agreement;
2. Common Crawl was disabled in the unknown-20 workflow.

V2 keeps discovery evidence separate from feed certification and fixes both issues.

## Current documented feed families

RexFeed / Product Feed Manager is currently published as the WordPress.org plugin slug best-woocommerce-feed and documents Google Merchant Center feed generation. Its feed configuration is controlled by the plugin, so V2 does not invent a filename.

WPFactory Product XML Feeds Manager currently documents XML Feed #1 with a default public filename of products.xml, while allowing the file path and name to be configured. V2 therefore uses /products.xml as a bounded documented candidate and requires other paths to be discovered.

SVMPForge Product Feed currently documents clean feed URLs of the form /apfw-feed/{unique-token}.xml. The token is random per feed, so V2 discovers it from public references/indexes and never enumerates token permutations.

Google for WooCommerce remains an API architecture without a separate feed URL. Its current documentation says the integration syncs through Google's API rather than a feed file.

## V2 corrections

- JavaScript/CSS/theme/plugin assets are excluded from feed-candidate learning.
- Query candidates are extracted only from actual URLs or HTML URL attributes.
- Native validation requires the mandatory Google fields inside one product item/entry.
- Common Crawl is enabled for the unknown cohort.
- Browser, HTTP API, sitemap, Wayback, and Common Crawl evidence remain provenance-separated.
- Random feed tokens are discovery targets only.
- 403/429/challenge responses remain transport-unverified rather than feed-negative.

## Target scope

The V2 runtime is limited to the 20 unknown-family calibration sites:

Aarna Computers, Ads Store, EZPZ Solutions, GamesNComps, hotshiftpc, ithunt, KC Computers, KRG KART, Kryptronix Gaming, NCL Computer, PC Kumar Infotech, PCHubShop, Prime ABGB, SCL Gaming, Variety Infotech, Viper PC, Cosmic Byte, Meckeys, StacksKB, Theproaudio.

Moskeys remains excluded because it is down/unresolvable. Only SSD remains separately established and outside this calibration cohort.

## Acceptance boundary

A native feed is accepted only when a current same-host payload contains the Google Merchant namespace and a complete product item with ID, title, link, and price.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, proxy-rotation evasion, or blind token enumeration is permitted.

## Current public research references

- WooCommerce Google for WooCommerce FAQ: https://woocommerce.com/document/google-for-woocommerce/faq/
- CTX Feed current feed management documentation: https://webappick.com/docs/ctx-feed/basic/manage-feeds/
- RexFeed WordPress.org listing: https://wordpress.org/plugins/best-woocommerce-feed/
- WPFactory current feed URL documentation: https://wpfactory.com/docs/generate-your-feed-and-find-its-url/
- SVMPForge WordPress.org listing: https://wordpress.org/plugins/svmpforge-product-feed-for-woocommerce/

V2 is an execution improvement, not a claim that every WooCommerce store publishes a public native Google Merchant XML file.
