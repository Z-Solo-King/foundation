# WooCommerce 30 Plugin-Family Grouping + Feed Guessing — 2026-09-30

The original 32-site corpus is reduced to 30 for this phase:
- Moskeys: excluded because the site is down/unresolvable.
- Only SDD: excluded because its native Google Merchant feed is already verified.

## Observed / historical feed-family grouping

| Feed family | Sites | Confidence |
|---|---|---:|
| WooCommerce Google Product Feed | PC Studio | High |
| CTX Feed / WebAppick | Quickin Computers | High |
| Product Feed PRO / AdTribes | Avikaretails | High |
| Google for WooCommerce / API-integrated | Geekbees; Ninja Dog; Network IT Store; My Nexus Infosys; Solanki Enterprises; AULA India | High |
| Product Feed Manager / WPPFM | IT Gadgets Online | High |
| Feed-generator family not identified | Aarna Computers; Ads Store; EZPZ Solutions; GamesNComps; hotshiftpc; ithunt; KC Computers; KRG KART; Kryptronix Gaming; NCL Computer; PC Kumar Infotech; PCHubShop; Prime ABGB; SCL Gaming; Variety Infotech; Viper PC; Cosmic Byte; Meckeys; StacksKB; Theproaudio | Not identified |

This yields 10 sites with a known feed/plugin family and 20 sites that have WooCommerce/plugin-stack evidence but no sufficiently strong feed-generator fingerprint. The latter must not be forced into a named family.

## Guessing order

For known feed families:
1. Explicit public references.
2. Public plugin output-directory XML links.
3. Documented family-specific endpoints.
4. Small generic fallback corpus.
5. Long-timeout retry only for higher-priority timed-out candidates.

For the 20 unknown-feed-generator sites:
1. Same public discovery.
2. All known plugin-family documented candidates as lower-priority hypotheses.
3. Generic XML fallback.
4. Strict current-payload validation.

For Google for WooCommerce sites, XML guessing is skipped unless an independent feed reference is discovered because Google for WooCommerce uses Google's Content API and does not provide a separate feed-file URL. citeturn441849search3

CTX Feed uses merchant-selected feed names and stores generated feeds under the Woo Feed uploads family, so directory/public-reference discovery is more informative than blind filename expansion. citeturn769041search0turn769041search2

Product Feed PRO stores generated static feeds under the Woo Product Feed Pro uploads folder, and current public examples show generated filenames can be opaque/random-looking. citeturn817178search0turn817178search3

WebToffee generates channel-specific feeds and exposes a generated feed URL; the feed name is configured by the merchant, so exact filenames are site-specific. citeturn441849search10turn441849search1

FeedCraft exposes a deterministic XML REST route at `/wp-json/feedcraft-product-feed/v1/xml`. citeturn441849search5

CodeSolz documents `wp-content/uploads/codesolz-feeds/google-products.xml`. citeturn441849search12

## Acceptance contract

A guessed URL is never evidence by itself. A native hit requires a current same-host payload with the Google Merchant namespace and a real product item containing `g:id`, `g:title`, `g:link`, and `g:price`. Sitemaps, normal RSS/Atom, Store API data, reconstructed XML, historical-only captures, and challenge pages do not qualify.

