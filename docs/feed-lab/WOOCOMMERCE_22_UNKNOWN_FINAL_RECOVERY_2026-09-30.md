# WooCommerce 22 Unknown Sites — Final Plugin/XML Recovery

Date: 2026-09-30
Plugin recovery runtime: GitHub Actions 36629019347
Final naming-only browser XML runtime: GitHub Actions 36667211627

Scope: 22 sites that remained `unknown_woocommerce` after the 31-site plugin fingerprint/grouping pass.

Method:
1. V175-derived public browser recovery for plugin assets/metadata.
2. Public technology-index corroboration where available.
3. Naming-only XML probing in the browser session.
4. No product catalog/API extraction.
5. No HTML/JS/XHR feed-URL mining.
6. No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, or stealth/evasion.

Coverage: 22/22 sites.
XML candidates: 47 per site (1034 candidate checks).
Native XML hits: 0.
Clean no-hit sites: 5.
Transport-limited sites: 17.

| Site | Browser | XML result | Transport-limited checks | Native feed |
|---|---:|---|---:|---|
| Aarna Computers | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 45 | none |
| Ads Store | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| AULA India | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 43 | none |
| Cosmic Byte | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 43 | none |
| EZPZ Solutions | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 1 | none |
| hotshiftpc | 200 | NO_NATIVE_FEED_VERIFIED | 0 | none |
| itgadgetsonline | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 1 | none |
| ithunt | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| KC Computers | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| KRG KART | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| Kryptronix Gaming | 200 | NO_NATIVE_FEED_VERIFIED | 0 | none |
| Meckeys | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 3 | none |
| Moskeys | 0 | NO_NATIVE_FEED_VERIFIED | 0 | none |
| NCL Computer | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| PC Kumar Infotech | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| PCHubShop | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 37 | none |
| Prime ABGB | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| SCL Gaming | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 37 | none |
| StacksKB | 200 | NO_NATIVE_FEED_VERIFIED | 0 | none |
| Theproaudio | 403 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| Variety Infotech | 200 | TRANSPORT_LIMITED_NO_NATIVE_FEED | 47 | none |
| Viper PC | 200 | NO_NATIVE_FEED_VERIFIED | 0 | none |

## Definitive findings

No new native Google Merchant XML feed was verified for any of the 22 unknown sites.
Five sites produced clean no-hit transport runs: hotshiftpc, Kryptronix Gaming, Moskeys, StacksKB, and Viper PC.
The other 17 sites were transport-limited during at least one candidate check, so their no-hit result is not equivalent to proof that no feed exists.

## Plugin evidence outcome

The V175 browser recovery recovered public plugin assets on 9 sites, but no known feed-plugin family was established. Several sites were independently corroborated as using other WooCommerce plugins, but those are not feed generators.

## Operational conclusion

The `unknown_woocommerce` group should remain unresolved rather than being assigned a feed family speculatively.
The next evidence-bearing step would require a stronger public plugin/configuration signal or site-owner/admin-side evidence for the 17 transport-limited sites. Blind expansion of the naming corpus is unlikely to add reliable information without new plugin/configuration evidence.