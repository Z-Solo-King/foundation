# WooCommerce V175 Unknown-Site Manifest — 2026-09-30

## Scope

Current unresolved cohort: 22 public WooCommerce retailers.

The canonical runner targets exactly these 22 sites and excludes the ten already-known sites. The workflow uses six independent shards and uploads one evidence JSON per shard.

V175 is the extraction authority for clearance-aware browser recovery, persistent-cookie reuse, browser/XHR discovery, transport/provenance separation, bounded recovery, and public-only acquisition.

## Final evidence classification

| Site | Public evidence state | Feed-plugin family | Notes |
|---|---|---|---|
| Aarna Computers | browser challenged | unknown | WooCommerce + Elementor surface; no feed-family signal recovered |
| Ads Store | plugin surface recovered | unknown | WooCommerce + Safe SVG; no feed-family signal |
| EZPZ Solutions | plugin surface recovered | unknown | Many WooCommerce extensions; no feed-family signal |
| GamesNComps | live Cloudflare Browser Run surface recovered | unknown | WooCommerce; current rendered HTML exposed no feed-family marker |
| hotshiftpc | plugin surface recovered | unknown | WooCommerce + Jet/Jet Woo extensions; no feed-family signal |
| ithunt | browser challenged | unknown | No plugin surface |
| KC Computers | browser challenged | unknown | No plugin surface |
| KRG KART | browser challenged | unknown | Browser Run returned a 403 surface with no plugin marker |
| Kryptronix Gaming | plugin surface recovered | unknown | WooCommerce + Easy Login/LiteSpeed/compare extensions; no feed-family signal |
| NCL Computer | browser challenged | unknown | No plugin surface |
| PC Kumar Infotech | plugin surface recovered | unknown | WooCommerce + product-builder/variation/wishlist/compare extensions; no feed-family signal |
| PCHubShop | browser challenged | unknown | No plugin surface |
| Prime ABGB | browser challenged | unknown | No plugin surface |
| SCL Gaming | browser challenged | unknown | No plugin surface |
| Variety Infotech | plugin surface recovered | unknown | WooCommerce + Cashfree/reviews/product-search extensions; no feed-family signal |
| Viper PC | plugin surface recovered | unknown | Public surface recovered; no feed-family signal |
| AULA India | browser reached / no plugin assets | unknown | 403 responses; public namespace hints did not identify a feed plugin |
| Cosmic Byte | browser challenged | unknown | No feed-family marker recovered |
| Meckeys | plugin surface recovered | unknown | WooCommerce + discount/filter/variation/product-search extensions; no feed-family signal |
| Moskeys | transport/DNS failure | unknown | ERR_NAME_NOT_RESOLVED in V175 browser pass |
| StacksKB | plugin surface recovered | unknown | WooCommerce + Ajax Search + LiteSpeed; no feed-family signal |
| Theproaudio | browser challenged | unknown | No plugin surface |

## Important result

No current 22-site target has a verified native Google Merchant feed from this evidence set, and no current target has a sufficiently strong plugin-family fingerprint to assign one of the known feed-generator families.

Do not classify these as no feed exists. The correct state is feed plugin/feed URL unresolved unless a native Merchant XML payload is independently validated.

The native-feed validator requires Google Merchant namespace plus real product fields such as g:id, g:title, g:link and g:price and rejects challenge pages/non-feed content.

## Recovery status

The runner is split into clean-browser, public API, passive-discovery, and direct-feed lanes. Browser evidence is collected with Chromium, Firefox/Gecko and WebKit in independent contexts; direct API/feed requests are cookie-free. Challenge/clearance state is diagnostic only and is never replayed or admitted into native-feed verification.

Cloudflare Browser Run remains an optional diagnostic lane. The current account is on Workers Free, so its low Browser Run limits make it unsuitable as a parallel 22-site execution dependency.

## Remaining blockers

1. Ten targets remain challenge-blocked for this acceptance path; the repository deliberately does not bypass those challenges.
2. Moskeys remains DNS-unresolvable from the GitHub runner, so it is transport-unresolved.
3. Cloudflare Browser Run remains quota-limited on the current Workers Free account, but it is no longer a required execution dependency.

The canonical `main` extraction run completed successfully and produced a validated aggregate, so there is no CI queue blocker remaining.

## Current completion state

22/22 targets are accounted for in canonical `main` run #11 (`e2dea16f0e52a23df475e8a46eaa1dbb9f18314d`).
0/22 feed-plugin families verified.
0/22 native Google Merchant feeds verified.
22/22 targets have deterministic evidence state and documented blocker/next state.
6/22 targets had an admissible, non-challenged browser path for native verification in this run; all six still produced zero native-feed validations.
16/22 targets were non-admissible because of challenge, transport, or lack of a clean 200 browser path.

The aggregate validator passed with exactly 22 rows and the known-ten exclusion assertion. GamesNComps is now included in the canonical 22-site run and no feed-family marker was recovered.