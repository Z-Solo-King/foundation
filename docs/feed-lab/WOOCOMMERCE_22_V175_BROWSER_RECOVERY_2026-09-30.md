# WooCommerce 22-site V175 Browser Recovery — 2026-09-30

## Scope

This lane covers the 22 sites still classified as `unknown_woocommerce` after the canonical 31-site plugin/XML hunt.

The uploaded extractor is V175. Its architecture defines a shared pipeline with transport, discovery, browser recovery, and learning owners; this recovery lane uses the browser/public-plugin portion only.

## Method

Public read-only browser recovery was used to:
- load the storefront homepage;
- inspect public `/wp-json/`, `/?rest_route=/`, and `/robots.txt`;
- fingerprint only public `/wp-content/plugins/<slug>` asset references and WordPress metadata;
- classify known feed-plugin slugs with a strict allowlist;
- reject common false positives such as `instagram-feed`.

Explicitly excluded:
- WooCommerce Store API/product catalog extraction;
- product reconstruction;
- feed URL extraction from HTML/JS/XHR;
- CAPTCHA solving;
- Cloudflare challenge bypass;
- clearance-cookie replay;
- authentication bypass;
- stealth/evasion.

## Runtime receipt

Successful complete runtime: GitHub Actions run **36628385149**.

Coverage: **22/22 sites**.

Results:
- **9** sites exposed public plugin assets, but **no feed-family signal** was recovered.
- **9** sites returned a browser/challenge surface with no usable plugin evidence.
- **4** sites were reachable but exposed no plugin assets on the tested public surfaces.
- **0** new documented WooCommerce feed-plugin families were identified.

## Recovered plugin evidence

| Site | Recovered public plugin assets |
|---|---|
| Aarna Computers | contact-form-7, elementor, elementor-pro, woocommerce |
| Ads Store | safe-svg, woocommerce |
| AULA India | none |
| Cosmic Byte | none |
| EZPZ Solutions | add-to-any, ajax-search-for-woocommerce-premium, colorlib-404-customizer, creame-whatsapp-me, customer-reviews-woocommerce, elementor, elementor-pro, iconic-woo-linked-variations-premium, product-gtin-ean-upc-isbn-for-woocommerce, smart-slider-3, wc-cart-pdf, woo-product-slider, woocommerce, woocommerce-additional-fees, woocommerce-ajax-filters, woocommerce-google-analytics-integration, wp-social, wpnotif, wt-smart-coupons-for-woocommerce, yith-woocommerce-brands-add-on-premium |
| hotshiftpc | jet-menu, jet-search, woocommerce |
| itgadgetsonline | advanced-ads, ajax-search-for-woocommerce-premium, back-in-stock-notifier-for-woocommerce, conditional-payments-for-woocommerce, ean-for-woocommerce, elementor, elementor-pro, essential-addons-for-elementor-lite, gutentor, kia-subtitle, ovic-addon-toolkit, woocommerce, woocommerce-google-analytics-integration, wpc-composite-products |
| ithunt | none |
| KC Computers | none |
| KRG KART | none |
| Kryptronix Gaming | no plugin asset recovered in this browser run; earlier public evidence still shows instagram-feed, which is not treated as a product-feed plugin |
| Meckeys | advanced-product-fields-for-woocommerce-pro, meckeys-blocks, meckeys-gst-input, meckeys-seo, neve-pro-addon, woo-discount-rules, woo-discount-rules-pro, woo-variation-swatches, woocommerce, woocommerce-additional-variation-images, woocommerce-back-in-stock-notifications, woocommerce-google-analytics-integration, woocommerce-product-search |
| Moskeys | none |
| NCL Computer | none |
| PC Kumar Infotech | click-to-chat-for-whatsapp, contact-form-7, js_composer, revslider, structured-content, table-of-contents-plus, variation-swatches-for-woocommerce, widget-google-reviews, woocommerce, woocommerce-product-builder, yith-woocommerce-compare, yith-woocommerce-wishlist |
| PCHubShop | none |
| Prime ABGB | none |
| SCL Gaming | none |
| StacksKB | ajax-search-for-woocommerce, litespeed-cache, woocommerce |
| Theproaudio | none |
| Variety Infotech | cashfree, customer-reviews-woocommerce, elementor, fluentform, google-site-kit, safe-svg, smart-slider-3, woocommerce, woocommerce-product-search-gt, wp-whatsapp |
| Viper PC | safe-svg |

## Interpretation

The 22-site browser lane materially improves the plugin evidence for the reachable sites, but it does not establish a new feed-plugin family.

Therefore the 22 sites remain `unknown_woocommerce` for feed-plugin grouping. This is an evidence classification, not proof that a feed plugin is absent.

The previously verified native Google Merchant XML feed remains **Only SDD**:
`https://onlyssd.com/?woocommerce_gpf=google`

## CI hardening

A 22-way sharded recovery workflow was added so one slow/blocked site cannot hold the entire lane. Its first execution produced all 22 per-site artifacts; the only failure was aggregation caused by flattening identical `recovery.json` filenames. The workflow was corrected to preserve per-site artifact directories.

Corrected rerun: **36629019347**.
