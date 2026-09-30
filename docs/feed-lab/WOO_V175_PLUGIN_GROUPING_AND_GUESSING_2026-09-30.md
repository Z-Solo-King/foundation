# WooCommerce V175 — Plugin Grouping, Research & Guessing Plan
_Date: 2026-09-30_

## 1. Current grouping

The completed canonical V175 run #14 contains 22 rows. For the active extraction cohort, Moskeys is excluded because the site is currently down/unresolvable.

The resulting 21-site grouping is:

| Group | Sites | Evidence |
|---|---|---|
| GLA / API-integrated | AULA India | Public `wc/gla` namespace; no standalone feed candidate |
| Challenge-blocked | Aarna Computers, Ads Store, GamesNComps, ithunt, KRG KART, NCL Computer, PC Kumar Infotech, PCHubShop, Prime ABGB, SCL Gaming, Variety Infotech, Cosmic Byte, Theproaudio | Challenge encountered; native verification must remain blocked by the acceptance boundary |
| Clean + feed-family unknown | EZPZ Solutions, hotshiftpc, Kryptronix Gaming, Meckeys, StacksKB, Viper PC | Clean browser evidence exists, but no known feed-plugin family was fingerprinted |
| HTTP access blocker | KC Computers | HTTP 403 without enough evidence to classify it as a challenge |

Run #14 baseline: 0/21 native XML feeds after excluding Moskeys, 1 API-integrated GLA site, 13 challenge-blocked, 6 clean-unknown, and 1 HTTP-403 case.

## 2. Plugin research findings

### WooCommerce Google Product Feed
Official WooCommerce documentation exposes the conventional file-feed model: the feed URL is shown in WooCommerce → Settings → Product Feeds. The extension also uses the query form `?woocommerce_gpf=google`, with `gpf_start` and `gpf_limit` available for partial feeds. citeturn777206search1turn777206search5

**Guessing rule:** probe the documented query endpoints first; they are low-complexity hypotheses, not proof.

### CTX Feed / WebAppick
The current WordPress.org instructions generate a Google Shopping XML feed and provide a feed URL. Public support examples show generated feeds under `/wp-content/uploads/woo-feed/google/xml/` and arbitrary feed filenames. citeturn777206search2turn211596search9

**Guessing rule:** inspect the public directory index and any page/source references; do not try to enumerate arbitrary filename strings.

### AdTribes Product Feed PRO
Current public support examples show feeds under `/wp-content/uploads/woo-product-feed-pro/xml/` with generated random-looking filenames. citeturn522876search3turn522876search6

**Guessing rule:** directory-index discovery or public references only. A random token cannot be safely inferred from a hostname.

### Product Feed Manager / WPPFM
WooCommerce documentation states that generated feeds are stored in `/wp-content/uploads/wppfm-feeds/` and that the feed list exposes the URL. citeturn623811search0

**Guessing rule:** inspect the public directory and any public references; do not assume a fixed filename.

### WebToffee Product Feed
WebToffee documentation confirms XML product-feed generation, Google Shopping support, and generated feed URLs. Public support examples place files under `/wp-content/uploads/webtoffee_product_feed/`, including `wt_fb_Feed.xml` style filenames. citeturn777206search13turn623811search1

**Guessing rule:** test documented casing/name patterns, then directory-index references.

### CodeSolz Merchant Feed Booster
Current WordPress.org documentation gives a deterministic Google feed path: `wp-content/uploads/codesolz-feeds/google-products.xml`. citeturn211596search0

**Guessing rule:** this is a fixed-path hypothesis and should be directly validated.

### FeedCraft
Current WordPress.org documentation exposes deterministic REST endpoints: `/wp-json/feedcraft-product-feed/v1/xml` and `/json`. citeturn522876search0

**Guessing rule:** this is a fixed REST hypothesis and should be directly validated.

## 3. What the current site evidence suggests

The clean sites do not currently expose an identifiable feed-generator slug:

- EZPZ Solutions exposes GTIN/identifier and WooCommerce extensions but no feed-plugin marker.
- hotshiftpc exposes a Jet/Crocoblock-heavy WooCommerce stack but no feed-plugin marker.
- Kryptronix exposes WooCommerce, comparison, reviews, and Instagram tooling but no feed-plugin marker.
- Meckeys exposes product-search, discount-rule and variation tooling but no feed-plugin marker.
- StacksKB exposes WooCommerce plus product-filter/search tooling but no feed-plugin marker.
- Viper PC exposes WooCommerce/Elementor/LiteSpeed-style infrastructure but no feed-plugin marker.

These are **not plugin identifications**. They are exclusion clues that keep the hypothesis set broad.

## 4. Guessing work now enabled

The next extractor pass will use this order:

1. Fixed native/feed-generator endpoints already documented by the plugin.
2. Public directory-index discovery for generated/random feed filenames.
3. Public HTML/XHR/source references to feed URLs.
4. Historical public references as discovery only.
5. Strict current-payload validation.

A hypothesis becomes a verified native feed only after the current response contains the Google Merchant namespace plus real product fields and remains same-host. A guessed URL returning HTML, a sitemap, Store API data, or a historical feed remains unverified.

## 5. Security boundary

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, credential use, stealth/anti-detect browser, or blind random-token enumeration is part of the guessing process.
