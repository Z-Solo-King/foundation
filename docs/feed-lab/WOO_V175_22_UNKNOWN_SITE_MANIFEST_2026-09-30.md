# WooCommerce V175 Unknown-Site Manifest — 2026-09-30

## Scope

Current **active** unresolved cohort: **21** public WooCommerce retailers.

Moskeys is explicitly excluded from the active extraction denominator because the site is currently down/unresolvable. The completed V175 run #14 included Moskeys historically in its 22-row artifact; this manifest filters that unavailable target out rather than treating it as an extraction failure.

The canonical runner still excludes the ten already-known sites. The extraction workflow uses six independent shards and current-run evidence is taken from canonical `main`.

V175 remains the extraction/design authority for browser recovery, browser/XHR discovery, transport/provenance separation, bounded recovery, and public-only acquisition.

## Run #14 evidence — canonical main

Run ID: `36686498909`  
Run head: `adab53eb74a02d9eac55f48413c7787dceef805e`  
All six extraction shards completed successfully and the aggregate job passed.

After excluding Moskeys, the 21 active targets classify as:

| Evidence state | Count | Meaning |
|---|---:|---|
| Google for WooCommerce / API-integrated | 1 | AULA India exposed `wc/gla`; treated as API-integrated, not an XML feed |
| Challenge-blocked | 13 | Challenge encountered; native verification is inadmissible under the acceptance boundary |
| Clean/admissible but feed-family unknown | 6 | A clean browser path existed, but no known feed-generator family or valid native Merchant XML was recovered |
| HTTP-blocked without a classified challenge | 1 | KC Computers returned HTTP 403 on all browser engines without enough evidence to classify the response as a Cloudflare challenge |
| **Active total** | **21** | — |

### Active site state

| Site | State |
|---|---|
| Aarna Computers | challenge-blocked |
| Ads Store | challenge-blocked |
| EZPZ Solutions | clean/admissible, unknown |
| GamesNComps | challenge-blocked |
| hotshiftpc | clean/admissible, unknown |
| ithunt | challenge-blocked |
| KC Computers | HTTP 403 / no clean 200; unclassified blocker |
| KRG KART | challenge-blocked |
| Kryptronix Gaming | clean/admissible, unknown |
| NCL Computer | challenge-blocked |
| PC Kumar Infotech | challenge-blocked |
| PCHubShop | challenge-blocked |
| Prime ABGB | challenge-blocked |
| SCL Gaming | challenge-blocked |
| Variety Infotech | challenge-blocked |
| Viper PC | clean/admissible, unknown |
| AULA India | Google for WooCommerce / API-integrated via `wc/gla` |
| Cosmic Byte | challenge-blocked |
| Meckeys | clean/admissible, unknown |
| StacksKB | clean/admissible, unknown |
| Theproaudio | challenge-blocked |

## Native-feed result

**0/21 active targets have a verified native Google Merchant XML feed in run #14.**

The native validator requires a real current payload containing the Google Merchant namespace plus product fields such as `g:id`, `g:title`, `g:link`, and `g:price`; challenge/non-feed payloads are rejected.

Do **not** convert a normal WooCommerce Store API response, product API, sitemap, RSS/Atom feed, historical URL, or reconstructed XML into a native Merchant-feed result.

## Important architecture finding: Google for WooCommerce

AULA India is the current concrete API-integrated case. The repository detected the public `wc/gla` namespace, with no standalone feed candidate.

This matches current WooCommerce documentation: Google for WooCommerce uses API-based product synchronization and does not expose a separate feed-file URL; the traditional feed-file path is a separate product-feed extension. WooCommerce also documents migration to the Google Merchant API. Therefore the extractor should classify a public `wc/gla` signal as **API-integrated** rather than continue forcing XML URL discovery.

## Current blockers and alternatives

1. **Target-side challenge protection — 13 active sites.** The repository must not solve CAPTCHAs, replay clearance cookies, or bypass anti-bot controls. The current alternative is evidence-preserving classification plus re-attempt only when the public site becomes accessible.
2. **KC Computers HTTP 403 — 1 active site.** No clean 200 was obtained and the response was not classified as a challenge. This remains an unresolved transport/access case, not a negative feed result.
3. **Unknown clean WooCommerce sites — 6 active sites.** Continue treating these as unresolved feed URL/family cases. The current V175 probe path already covers browser request/resource discovery, public API surfaces, passive indexes, historical URL hints, and bounded direct feed validation.
4. **Cloudflare Browser Run.** It remains diagnostic only. Current Cloudflare Workers Free limits are 10 browser minutes/day, 3 concurrent Browser Sessions, and 1 Quick Action request per 10 seconds, so it is not a scalable parallel dependency for this cohort.

## Completion semantics

The extraction sweep is complete for the **21 active targets** represented by run #14 after the explicit Moskeys exclusion.

The remaining 20 active cases are not evidence of “no feed exists”; they are either blocked or unresolved under the public-only acceptance boundary. The next meaningful acceptance event for any of them is a current, publicly retrievable and independently validated Merchant XML payload, or a concrete plugin/API architecture signal that changes the transport classification.


## Addendum — acceptance fix identified after run #14

Run #14 is a valid baseline, but its implementation had one conservative blocker: any browser challenge caused the extractor to skip all direct native-feed probes for that site.

The V175 public-only boundary does not require that behavior. A feed endpoint can be independently public even when the homepage is challenged. The fix in PR #1594 now keeps feed requests cookie-free and permits native-feed verification only when the **feed payload itself** passes the strict current-payload validator and remains same-host. Homepage challenge evidence is still recorded and no challenge/clearance state is reused.
