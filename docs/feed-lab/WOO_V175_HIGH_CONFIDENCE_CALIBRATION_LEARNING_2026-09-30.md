# WooCommerce V175 Feed Calibration — Phase 1 (10 Sites) — 2026-09-30

## Correct Phase 1 boundary

The Phase 1 calibration cohort is 10 feed-related sites:

### Standalone feed-generator families (4)
- PC Studio — WooCommerce Google Product Feed
- Quickin Computers — CTX Feed / WebAppick
- Avikaretails — Product Feed PRO / AdTribes
- IT Gadgets Online — Product Feed Manager / WPPFM

### Google-for-WooCommerce / Google Listings & Ads family (6)
- Geekbees
- Ninja Dog
- Network IT Store
- My Nexus Infosys
- Solanki Enterprises
- AULA India

OnlySSD is excluded because its native Google feed was already separately established. Moskeys is excluded because the site is down.

## Calibration objective

This phase learns two distinct feed behaviors:
1. Standalone XML generator discovery and strict current-payload validation.
2. Google-for-WooCommerce family detection, distinguishing API-integrated synchronization from a separately published XML feed.

The harness uses browser/XHR/resource discovery, public REST namespace discovery, robots/sitemap discovery, public output-directory discovery, historical URL discovery, plugin-specific candidates, and bounded fallbacks. Challenge/clearance state is diagnostic only.

## Learning records

Each site records:
- expected vs detected family and confidence
- standalone native-feed verification status
- explicit and query feed references
- output-directory candidates
- historical candidate URLs
- browser engines, XHR/resource URLs, plugin assets and namespaces
- response patterns and candidate source/rank

For Google-for-WooCommerce, absence of a standalone XML feed is not treated as an extraction failure when the family is positively identified and no independent public feed URL is observed.

## Transfer to the unknown 20

After this 10-site calibration, learned URL grammars and evidence patterns are transferred to the unknown 20. Priority order:
1. exact public feed reference
2. browser/XHR/resource evidence
3. public plugin output directory
4. historical feed URL followed by current validation
5. plugin-specific documented URL grammar
6. generic filename guessing

No random filename enumeration is promoted above observed evidence, and 403/challenge/404 HTML/sitemap/RSS responses are not treated as proof of feed absence.

## Acceptance

A standalone feed is accepted only when the current payload itself validates as Google Merchant XML with the required namespace and core product fields.
