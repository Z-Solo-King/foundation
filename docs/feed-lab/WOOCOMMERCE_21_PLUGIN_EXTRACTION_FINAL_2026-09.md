# WooCommerce 21-site plugin extraction — final merged evidence

Canonical channel run: **36670300940** (21/21 successful)
V175 cross-check run: **36670267961** (21/21 successful)

Scope: plugin identification first. Evidence channels were Playwright homepage execution, browser XHR/Fetch metadata, homepage HTML plugin assets, WP-JSON, WordPress REST, WooCommerce REST v1/v2/v3 capability probes, and minimal product-route probes using `_fields=id` with response bodies not retained as product records.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, or product-catalog extraction was used for this plugin-identification lane.

## Final coverage

- Sites: **21/21**
- Sites with plugin assets in merged evidence: **12/21**
- Sites with feed-family signals: **0/21**
- Channel-run WC v1 reachable: **8**
- Channel-run WC v2 reachable: **9**
- Channel-run WC v3 reachable: **8**

## Site result

| Site | Channel status | Plugin assets (merged) | Feed family | XHR | WC v1 | WC v2 | WC v3 |
|---|---|---:|---|---:|---|---|---|
| Aarna Computers | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 4 | none | 86 | [0] | [0, 200] | [0] |
| Ads Store | PLUGIN_SURFACE_EXTRACTED | 3 | none | 15 | [403] | [403] | [403] |
| AULA India | PUBLIC_SURFACE_REACHED_NO_PLUGIN_ASSETS | 0 | none | 0 | [200, 403] | [200, 403] | [200, 403] |
| Cosmic Byte | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 3 | [200, 403] | [200, 403] | [200, 403] |
| EZPZ Solutions | PLUGIN_SURFACE_EXTRACTED | 20 | none | 101 | [200] | [200] | [200] |
| hotshiftpc | PLUGIN_SURFACE_EXTRACTED | 7 | none | 12 | [200] | [200] | [200] |
| ithunt | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 3 | [403] | [403] | [403] |
| KC Computers | PUBLIC_SURFACE_REACHED_NO_PLUGIN_ASSETS | 0 | none | 0 | [403] | [403] | [403] |
| KRG KART | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 3 | [403] | [403] | [403] |
| Kryptronix Gaming | PUBLIC_SURFACE_REACHED_NO_PLUGIN_ASSETS | 20 | none | 91 | [0, 200] | [0, 200] | [200] |
| Meckeys | PLUGIN_SURFACE_EXTRACTED | 13 | none | 72 | [200] | [200] | [200] |
| Moskeys | PUBLIC_SURFACE_REACHED_NO_PLUGIN_ASSETS | 0 | none | 0 | [0] | [0] | [0] |
| NCL Computer | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 1 | none | 7 | [403] | [403] | [403] |
| PC Kumar Infotech | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 13 | none | 41 | [403] | [403] | [403] |
| PCHubShop | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 0 | [403] | [403] | [403] |
| Prime ABGB | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 2 | none | 7 | [403] | [403] | [403] |
| SCL Gaming | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 1 | [403] | [403] | [403] |
| StacksKB | PLUGIN_SURFACE_EXTRACTED | 3 | none | 2 | [200] | [0, 200] | [0, 200] |
| Theproaudio | BROWSER_CHALLENGE_WITH_PUBLIC_API_SURFACE | 0 | none | 3 | [403] | [403] | [403] |
| Variety Infotech | PLUGIN_SURFACE_EXTRACTED | 10 | none | 51 | [403] | [403] | [403] |
| Viper PC | PLUGIN_SURFACE_EXTRACTED | 4 | none | 32 | [200] | [200] | [200] |

## Merged plugin evidence

- Aarna Computers: contact-form-7, elementor, elementor-pro, woocommerce; namespace: elementor/v1/feedback
- Ads Store: elementor, safe-svg, woocommerce
- EZPZ Solutions: add-to-any, ajax-search-for-woocommerce-premium, colorlib-404-customizer, creame-whatsapp-me, customer-reviews-woocommerce, elementor, elementor-pro, iconic-woo-linked-variations-premium, product-gtin-ean-upc-isbn-for-woocommerce, smart-slider-3, wc-cart-pdf, woo-product-slider, woocommerce, woocommerce-additional-fees, woocommerce-ajax-filters, woocommerce-google-analytics-integration, wp-social, wpnotif, wt-smart-coupons-for-woocommerce, yith-woocommerce-brands-add-on-premium
- hotshiftpc: elementor, jet-blocks, jet-menu, jet-search, jet-woo-product-gallery, litespeed-cache, woocommerce; namespaces: elementor/v1/feedback, jet-woo-builder-api/v1, jet-woo-product-gallery-api/v1
- Kryptronix Gaming: checkout-upsell-and-order-bumps, contact-form-7, customer-reviews-woocommerce, easy-login-woocommerce, elementor, elementor-pro, essential-addons-for-elementor-lite, hostinger-reach, instagram-feed, litespeed-cache, mailchimp-for-wp, make-column-clickable-elementor, quick-buy-now-button-for-woocommerce, widget-google-reviews, woo-smart-compare, woo-smart-quick-view, woo-smart-wishlist, woocommerce, wp-job-openings, yith-woocommerce-ajax-navigation
- Meckeys: advanced-product-fields-for-woocommerce-pro, meckeys-blocks, meckeys-gst-input, meckeys-seo, neve-pro-addon, woo-discount-rules, woo-discount-rules-pro, woo-variation-swatches, woocommerce, woocommerce-additional-variation-images, woocommerce-back-in-stock-notifications, woocommerce-google-analytics-integration, woocommerce-product-search
- NCL Computer: litespeed-cache
- PC Kumar Infotech: click-to-chat, click-to-chat-for-whatsapp, contact-form-7, js_composer, revslider, structured-content, table-of-contents-plus, variation-swatches-for-woocommerce, widget-google-reviews, woocommerce, woocommerce-product-builder, yith-woocommerce-compare, yith-woocommerce-wishlist
- Prime ABGB: js_composer, litespeed-cache
- StacksKB: ajax-search-for-woocommerce, litespeed-cache, woocommerce; namespace: woocommerce-email-editor/v1
- Variety Infotech: cashfree, customer-reviews-woocommerce, elementor, fluentform, google-site-kit, safe-svg, smart-slider-3, woocommerce, woocommerce-product-search-gt, wp-whatsapp
- Viper PC: elementor, elementor-pro, litespeed-cache, safe-svg; namespace: elementor/v1/feedback

## Result

No feed-plugin family was established across these 21 sites by the completed extraction lanes. This is not evidence that no feed plugin exists; it means no known feed family was established from the permitted public plugin/API/XHR evidence.

XML probing should now be driven only by newly established feed-family evidence rather than by another broad blind guess pass.
