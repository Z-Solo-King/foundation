# WooCommerce 32-Site Plugin Fingerprint → XML Guess Hunt

## Requested workflow

1. Extract plugin-related public information for all 32 WooCommerce retailers.
2. Group retailers that expose the same feed-plugin family.
3. Research the feed URL mechanics for each plugin family.
4. Generate bounded XML feed URL guesses from those mechanics and the existing project XML corpus.
5. Validate only the guessed XML responses as native Google Merchant feeds.

## Stage 1: plugin information only

Public surfaces used:
- homepage HTML
- public WordPress JSON index
- robots.txt
- public WordPress plugin asset names

This stage does not request WooCommerce product data. It does not call /wp-json/wc/store/v1/products, Shopify product APIs, product GraphQL APIs, or authenticated APIs.

## Stage 2: XML guessing

The XML stage does not consume explicit feed URLs discovered from site HTML, robots, or directory indexes. It uses deterministic guesses.

### WooCommerce Google Product Feed
Guesses use `woocommerce_gpf=google`, the `/woocommerce_gpf/google` permalink form, and bounded `gpf_start` / `gpf_limit` variants.
WooCommerce documents the base route and partial-feed parameters.
https://woocommerce.com/document/google-product-feed-feed-generation-options/

### CTX Feed / WebAppick
Guesses use the `woo-feed` uploads family plus the documented `woo_feed=<name>&wt=xml` query convention and a bounded set of conventional feed names.
CTX Feed documents files below `wp-content/uploads/woo-feed/[format]/[feed-name].[ext]` and live query-style feed URLs.
https://webappick.com/docs/ctx-feed/basic/manage-feeds/
https://webappick.com/docs/ctx-feed/merchants/how-to-make-and-upload-product-feed-to-facebook-business-manager/

### Product Feed PRO / AdTribes
Guesses use `wp-content/uploads/woo-product-feed-pro/` with conservative Google XML filenames and gzip variants.
AdTribes documents static feed files in this uploads directory.
https://adtribes.io/knowledge-base/cache-plugin-compatibility-with-product-feed-pro/

### WebToffee Product Feed
Guesses use `wp-content/uploads/webtoffee_product_feed/` with bounded Google feed filenames and gzip variants.
WebToffee documents XML/CSV feed generation, Google Shopping support, and generated feed URLs.
https://www.webtoffee.com/docs/product-feed-basic/webtoffee-product-feed-sync-basic-setup-guide/

### WPFM / Woo Product Feed Manager
Guesses use `wp-content/uploads/wppfm-feeds/` and common Google feed names.
The product-feed manager documentation describes generated feed URLs and manual channel submission.
https://woocommerce.com/document/product-feed-manager/submit-to-marketing-channels/

### Codesolz
Guess includes `wp-content/uploads/codesolz-feeds/google-products.xml`.
The plugin documentation exposes that Google feed file convention.
https://wordpress.org/plugins/merchant-feed-booster-lite-for-woocommerce/

### FeedCraft
XML guesses include `/wp-json/feedcraft-product-feed/v1/xml` and related XML forms.
The plugin listing documents its XML feed route for Google Merchant Center.
https://en-gb.wordpress.org/plugins/thebasics-product-feed/

### Google for WooCommerce
A `google-listings-and-ads` fingerprint is recorded as an API-sync family. The XML guess phase does not assume that this plugin must have a traditional feed URL.
WooCommerce states that Google for WooCommerce uses Google's shopping API and has no separate feed-file URL.
https://woocommerce.com/document/google-for-woocommerce/faq/

## Validation

A guessed URL counts as a native feed only when the response contains:
- Google Merchant namespace `http://base.google.com/ns/1.0`
- at least one `item` or `entry`
- `g:id`
- `g:title`
- `g:link`
- `g:price`

Sitemaps, generic RSS/XML, challenge pages, CAPTCHAs, and ordinary HTML are rejected.

## Output

`plugin-fingerprints.tsv` contains the 32-site plugin evidence.
`plugin-groups.md` groups sites by primary plugin signal.
`verified-native-feed-urls.tsv` contains only successfully validated native XML feed hits.
`*.miss` records sites for which none of the bounded XML guesses was validated.

All acquisition is public read-only. No authentication, CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, credential access, proxy rotation, or stealth/evasion is used.