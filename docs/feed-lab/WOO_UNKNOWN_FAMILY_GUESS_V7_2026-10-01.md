# WooCommerce Unknown Family Guess V7 — 2026-10-01

This wave follows V6 after an important live-run finding: high parallelism caused large timeout/challenge amplification, while many HTTP 200 results were HTML fallbacks rather than feeds.

V7 changes only the guessing/transport strategy:
- lower per-target concurrency (4) and 5s timeout;
- recover historically published same-host feed URLs from the Wayback CDX API;
- recover same-host URL references from the latest Common Crawl index;
- infer a feed-generator family from recovered URL grammar;
- re-probe recovered URLs against the current site before accepting them;
- retain the existing bounded family grammar matrix.

No page crawling, plugin extraction, Store API extraction, authentication, CAPTCHA/challenge bypass, clearance-cookie replay, proxy rotation, or random token enumeration is used.

Native acceptance remains current same-host HTTP 200 XML with the Google Merchant namespace and g:id, g:title, g:link and g:price in the same item/entry.

The 17-site unknown cohort is unchanged.