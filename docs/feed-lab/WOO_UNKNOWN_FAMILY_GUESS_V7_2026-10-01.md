# WooCommerce Unknown Family Guess V7 — 2026-10-01

This V7 rerun is anchored to source commit 94a5b5dfeb17f18239ac5defba72021aeb542ce2. V6 showed that broad parallel URL matrices amplified transport blocking, so this wave changes acquisition shape rather than increasing guesses.

## Execution contract

- 17 true-unknown targets, six independent shards.
- One representative public URL per researched feed family per target.
- Low per-target expansion concurrency: 2.
- 403/429/timeouts are retried independently with slow delays; no evasion.
- A family expands only after its representative returns a stable public HTTP 200 response that is useful as a feed-family signal.
- 200 HTML fallbacks are transport-reachable but not treated as useful feed-family evidence.
- No Store API extraction, plugin extraction, browser/XHR discovery, authentication, CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, proxy rotation, or random token enumeration.
- Native certification remains strict current same-host HTTP 200 XML/RSS/Atom-like payload with Google Merchant namespace and g:id, g:title, g:link and g:price inside the same item or entry.

## Researched families

WooCommerce Google Product Feed; CTX/WebAppick; AdTribes Product Feed PRO; WPFM/Product Feed Manager; WebToffee Product Feed; CodeSolz Merchant Feed Booster; FeedCraft; RexFeed; KLPSoft; iCopyDoc.

## Interpretation

A transport block is not a feed negative. A family signal is evidence for V8 family identification, not final plugin identity. Only a current validated Merchant XML payload can satisfy the native-feed objective.
