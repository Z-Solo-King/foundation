# WooCommerce Unknown 20 — Historical Refinement Learning — 2026-09-30

The first learned-pass result kept all 20 unknown sites at low-confidence `unknown_woocommerce`. This is not sufficient to conclude that no feed generator exists.

This refinement adds an independent evidence layer:

1. query Wayback CDX for feed-like URLs and WordPress plugin assets;
2. fetch a bounded set of archived HTML snapshots;
3. recover historical plugin slugs, REST namespaces and explicit feed URLs;
4. revalidate recovered feed URLs against the current site;
5. treat an archive-only feed path as historical evidence unless the current payload validates;
6. keep RSS/category/product `/feed/` URLs out of Merchant-feed candidates;
7. retain the public-only/no-cookie-replay/no-challenge-bypass boundary.

A current native feed is accepted only from the current payload validator, not from archived content alone.
