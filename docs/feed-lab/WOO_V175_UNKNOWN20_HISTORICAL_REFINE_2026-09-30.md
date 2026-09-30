# WooCommerce V175 — Unknown 20 Historical Refinement — 2026-09-30

## Purpose

The initial learned pass left all 20 unknown sites at low-confidence `unknown_woocommerce`. That result is a statement about the available current fingerprint evidence, not proof that the sites lack a feed generator.

The historical refinement adds a separate evidence layer that searches for prior public feed/plugin references and then tests whether any recovered URL still works today.

## Execution model

The unknown 20 were split across six parallel shards. The historical stage:

1. queried Internet Archive CDX for feed-like URLs and WordPress plugin assets;
2. fetched a bounded set of archived HTML snapshots;
3. recovered historical plugin slugs, REST namespaces and explicit feed-like URLs;
4. kept only same-host feed-like references;
5. revalidated recovered candidate URLs against the current site;
6. excluded ordinary WordPress RSS/Atom feed paths from Merchant-feed candidates;
7. retained archive-only evidence as hypothesis input rather than current verification.

Historical refinement is HTTP-only in its current implementation; it no longer installs a browser runtime.

## Authoritative post-classifier result

The latest corrected six-shard dataset analyzed **333 archived HTML snapshots** and produced **112 historical feed-like candidates**.

Current low-confidence family hypotheses:

| Site | Hypothesis | Historical evidence | Current native XML |
|---|---|---|---|
| Kryptronix Gaming | WebToffee Product Feed | WebToffee fingerprint | not verified |
| NCL Computer | WebToffee Product Feed | WebToffee fingerprint | not verified |
| Prime ABGB | WooCommerce Google Product Feed | `woocommerce_gpf` fingerprint | not verified |
| Variety Infotech | Google for WooCommerce / GLA | `google-listings-and-ads` fingerprint | not verified |

The other **16/20** remain `unknown_woocommerce`.

The authoritative result therefore contains:
- 2 WebToffee hypotheses;
- 1 WooCommerce GPF hypothesis;
- 1 Google-for-WooCommerce hypothesis;
- 16 unresolved;
- 0/20 current native standalone Google Merchant XML feeds verified.

## Why historical evidence is not final

Archive captures can be stale, can contain plugin traces from a previous site configuration, and can preserve URLs that no longer exist.

Therefore:
- historical plugin evidence may identify the family;
- a historical XML URL may become a current candidate;
- only the current response may certify a native feed.

HTTP 403/429, challenge HTML and 404 HTML are recorded as transport/response states, not as proof of feed absence.

## Reusable refinement rule

For an unresolved WooCommerce site:

`current fingerprint → bounded historical family evidence → same-host candidate recovery → current revalidation → confidence/state update`

Do not convert a historical family hypothesis into a production feed result without a current valid Merchant payload.
