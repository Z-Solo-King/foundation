# WooCommerce Google Feed Recovery — Canonical Audit Handoff

Date: 2026-09-26
Branch: `ai/woocommerce-google-feed-audit-20260926`
Latest adaptive-fix commit: `0fe4e2f0b5ddbcb8d0e2cb820c3f472ddd58da20`

## Scope

31 WooCommerce retailers were audited for public Google Merchant/product-feed XML recovery.

Only SDD was intentionally excluded from this audit, per the task scope. Its previously verified native WooCommerce Google Product Feed remains separate and must not be mixed into this 31-site result set.

## Final result

| Result | Count |
|---|---:|
| WooCommerce sites audited | 31 |
| Native Google Merchant XML feeds verified | 0 |
| Full public Store API backup XMLs | 19 |
| Partial public Store API backup XMLs | 3 |
| Sites still publicly blocked/geo/unavailable | 9 |
| XML backup files produced | 22 |
| XML product items captured | 24,050 |

The 22 XML files are Google Merchant-compatible **backup snapshots reconstructed from publicly accessible WooCommerce Store API data**. They are not being represented as the retailers' native Google feed URLs.

Representative full catalogs recovered include:
- Prime ABGB — 5,806 products
- EZPZ Solutions — 4,946
- GamesNComps — 2,851
- PC Studio — 2,468
- ITGadgetsOnline — 1,373
- Avika Retails — 1,125
- Meckeys — 1,062
- Kryptronix Gaming — 910
- Nexus Infosys — 716
- Aarna Computers — 603

Partial backups:
- Ads Store — 3-product snapshot
- NetworkITStore — 3-product snapshot
- Ninja Dog — 3-product snapshot

## Remaining 9

These are **not** classified as "no feed". They remain unresolved because available public execution paths hit Cloudflare challenges, geographic denial, or network unavailability:

1. ithunt
2. kccomputers
3. KRG KART
4. PC Kumar Infotech
5. PCHubShop
6. SCL Gaming
7. Variety Infotech
8. Moskeys
9. Theproaudio

Native XML may still exist behind protected routes; the audit has not established its absence.

## Execution strategy now in use

The final optimized rescue architecture is deliberately public-only and blocker-resistant:

1. Race four public WooCommerce Store API forms:
   - `/wp-json/wc/store/v1/products`
   - `/wp-json/wc/store/v1/products/`
   - `/?rest_route=/wc/store/v1/products`
   - `/index.php?rest_route=/wc/store/v1/products`
2. Use a tiny seed request before expensive pagination.
3. After the first successful public catalog endpoint, paginate at up to 100 products/page, with adaptive continuation when pagination headers are absent.
4. Run native Google-feed path candidates concurrently when the Store API is unavailable.
5. Avoid Playwright/browser installation in the optimized rescue workflow.
6. Do not use CAPTCHA solving, Cloudflare challenge bypass, credential access, proxy rotation, clearance-cookie replay, or stealth anti-bot evasion.
7. Preserve blocked/challenged results as unresolved rather than falsely classifying them as feed absence.
8. Temporary duplicate WooCommerce feed workflows were changed to manual dispatch on the audit branch so a single push does not fan out into multiple competing scans.

The optimized rescue run completes in roughly a minute once a GitHub runner is allocated.

## Continuation rule for the next chat

Start from branch `ai/woocommerce-google-feed-audit-20260926` at commit `0fe4e2f0b5ddbcb8d0e2cb820c3f472ddd58da20`.

Do not restart the 31-site full scan.

Focus only on the remaining nine, using additional public/authorized discovery sources and transport variations. Keep native-feed URLs separate from reconstructed Store API backups.

The project objective remains: maximize verified public Google Merchant XML/feed recovery and produce durable backup artifacts without bypassing third-party access controls.
