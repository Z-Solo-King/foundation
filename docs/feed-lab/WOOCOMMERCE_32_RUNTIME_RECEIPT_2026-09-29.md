# WooCommerce 32-Site Plugin → XML Guess Runtime Receipt

Run: GitHub Actions run 36615157789
Artifact: native-google-feed-url-results
Artifact ID: 11055712306
Executed head: 43d9010230e52331cc079cd977758fb3cdd176d5

## Coverage

- 32 / 32 retailers produced plugin-fingerprint records.
- 32 / 32 retailers produced an XML-guess outcome.
- Native feed validation passed for 1 retailer.
- 31 retailers had no native feed verified by the bounded guess corpus.

## Plugin groups

### adtribes_product_feed_pro
- avikaretails

### ctx_feed_webappick
- quickincomputers

### google_for_woocommerce
- Geekbees
- Ninja Dog
- nexusinfosys
- solankienterprises

### unknown_woocommerce
- AULA India
- Aarna Computers
- Ads Store
- Cosmic Byte
- EZPZ Solutions
- GamesNComps
- KC Computers
- KRG KART
- Kryptronix Gaming
- Meckeys
- Moskeys
- NCL Computer
- Only SDD
- PC Kumar Infotech
- PC Studio
- PCHubShop
- Prime ABGB
- SCL Gaming
- StacksKB
- Theproaudio
- Variety Infotech
- Viper PC
- hotshiftpc
- itgadgetsonline
- ithunt
- networkitstore

## Verified native XML feed

| Retailer | Guessed XML URL | Result |
|---|---|---|
| Only SDD | https://onlyssd.com/?woocommerce_gpf=google | NATIVE_FEED_VERIFIED |

The workflow's validator required the Google Merchant namespace plus product-item fields g:id, g:title, g:link, and g:price. Sitemaps/interstitials were rejected.

## Important interpretation

unknown_woocommerce means no feed-plugin fingerprint was detected in the public homepage / public WordPress JSON index surfaces used by this run. It does not mean no plugin is installed.

NO_NATIVE_FEED_VERIFIED means that none of the bounded XML guesses returned a payload accepted by the native validator during this run. It does not prove that a feed does not exist, especially for stores returning 403, timeouts, or challenge pages.

Google for WooCommerce signals are recorded separately because WooCommerce documents API-based product synchronization without a separate traditional feed-file URL.

## Method boundary

The runtime used plugin information extraction only in stage 1 and XML URL guessing only in stage 2. It did not extract product catalogs through WooCommerce Store API, Shopify product APIs, or product GraphQL endpoints.

Public read-only acquisition only. No authentication, CAPTCHA solving, challenge bypass, clearance-cookie replay, credential access, proxy rotation, or stealth/evasion.