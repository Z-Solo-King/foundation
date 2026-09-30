# WooCommerce V175 Active-Cohort Manifest — 2026-09-30

## Scope

The canonical recovery cohort is now **21 active public WooCommerce retailers**. Moskeys is explicitly excluded because the site is currently down / DNS-unresolvable from the extraction environment and is not useful as an active feed-recovery target.

The repository retains the ten previously-known exclusions separately. The extraction workflow uses six independent shards and validates the aggregate against this 21-site active host set.

V175 is the extraction authority for clearance-aware browser recovery, persistent-cookie semantics, browser/XHR discovery, transport/provenance separation, bounded recovery, and public-only acquisition. Challenge/clearance state is diagnostic only and is never replayed or admitted into native-feed verification.

## Canonical run

- Workflow: **WooCommerce V175 22 Plugin Extraction** (active cohort semantics; legacy workflow filename retained for compatibility)
- Run: **#14**
- Run ID: **36686498909**
- Head SHA: **adab53eb74a02d9eac55f48413c7787dceef805e**
- Aggregate artifact: `woocommerce-v175-plugin-aggregate`
- Aggregate validation: passed
- Active targets: **21**
- Verified native Google Merchant XML feeds: **0**
- Feed-generator families verified with a native feed URL: **0**
- Google for WooCommerce API-integrated targets: **1**
- Challenge-unverified targets: **13**
- Clean 200 browser targets still unresolved: **6**
- Non-challenge HTTP 403 targets: **1** (KC Computers)
- Excluded/down target: **1** (Moskeys)

## Final evidence classification

| Site | Public evidence state | Feed-plugin family | Transport / interpretation |
|---|---|---|---|
| Aarna Computers | challenge-unverified | unknown | standalone XML candidate probe skipped because challenge makes native verification inadmissible |
| Ads Store | challenge-unverified | unknown | standalone XML candidate probe skipped |
| EZPZ Solutions | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| GamesNComps | challenge-unverified | unknown | standalone XML candidate probe skipped |
| hotshiftpc | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| ithunt | challenge-unverified | unknown | standalone XML candidate probe skipped |
| KC Computers | HTTP 403 without challenge marker | unknown | public API/browser surface remained blocked; no native verification |
| KRG KART | challenge-unverified | unknown | standalone XML candidate probe skipped |
| Kryptronix Gaming | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| NCL Computer | challenge-unverified | unknown | standalone XML candidate probe skipped |
| PC Kumar Infotech | challenge-unverified | unknown | standalone XML candidate probe skipped |
| PCHubShop | challenge-unverified | unknown | standalone XML candidate probe skipped |
| Prime ABGB | challenge-unverified | unknown | standalone XML candidate probe skipped |
| SCL Gaming | challenge-unverified | unknown | standalone XML candidate probe skipped |
| Variety Infotech | challenge-unverified | unknown | standalone XML candidate probe skipped |
| Viper PC | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| AULA India | API surface recovered; homepage browser returned 403 with Cloudflare bot cookie | google_for_woocommerce | API-integrated via public `wc/gla`; no standalone XML expected from current evidence |
| Cosmic Byte | challenge-unverified | unknown | standalone XML candidate probe skipped |
| Meckeys | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| StacksKB | clean browser | unknown | standalone XML candidates probed; no native feed validated |
| Theproaudio | challenge-unverified | unknown | standalone XML candidate probe skipped |

## Important result

Run #14 is a successful **evidence-completion run**, not a claim that the remaining unknown sites have no feeds.

The current evidence establishes one distinct architecture change: **AULA India exposes the Google for WooCommerce integration through the public `wc/gla` WordPress REST namespace**, and the harness therefore classifies it as `google_for_woocommerce / api_integrated` rather than attempting to invent or reconstruct an XML feed.

The remaining six clean-browser targets have public WooCommerce surfaces but no sufficiently strong known feed-generator fingerprint and no current native Google Merchant payload passing the strict validator.

The 13 challenge-unverified targets remain unresolved by design. The repository does not bypass Cloudflare/CAPTCHA, replay clearance cookies, or treat challenge pages as feed evidence.

## Acceptance rule

A native Google Merchant feed is verified only when the **current public payload** independently validates with:

- Google Merchant namespace;
- RSS/Atom item/entry structure;
- product fields including `g:id`, `g:title`, `g:link`, and `g:price`;
- no challenge / CAPTCHA / access-denied payload.

Sitemaps, robots.txt, WooCommerce Store API responses, normal product APIs, historical URLs, or reconstructed XML are discovery evidence only and are never promoted to a native Merchant feed.

## Blocker assessment

1. **Target-side challenge controls:** still the dominant blocker for 13 active sites. Further repository-side probing cannot legitimately turn those into verified feeds without crossing the acceptance boundary.
2. **Clean unknowns:** six sites were reachable with clean browser passes but exposed no known feed-family signal and no verified current Merchant XML. The current candidate-mining/probe budget is therefore sufficient for this cohort unless a new site-specific signal appears.
3. **HTTP 403 without challenge marker:** KC Computers remains transport-blocked. It should not be labeled as feed-absent.
4. **Google for WooCommerce:** API-integrated architecture is now handled as a separate mode. Without Merchant account authorization, there is no public standalone Google feed URL to extract from the plugin itself.
5. **Cloudflare Browser Run:** remains optional diagnostic only; the current Free-plan limits make it unsuitable as a 21-site execution dependency.

## Completion state

**21/21 active targets are accounted for in canonical main run #14.**

- 0/21 native Google Merchant XML feeds verified
- 0/21 native feed-generator families verified by current feed payload
- 1/21 Google for WooCommerce API-integrated
- 13/21 challenge-unverified
- 6/21 clean-but-unknown
- 1/21 transport-blocked by HTTP 403
- 1 down site (Moskeys) explicitly excluded from the active cohort

The extraction implementation is complete for the active cohort under the repository's public-only acceptance contract. Remaining work is target-side re-access / authenticated Merchant evidence for blocked or API-integrated sites, not another generic feed-URL guessing pass.
