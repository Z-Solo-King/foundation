# WooCommerce Native Google Merchant Feed URLs — 2026-09-27

This registry contains **only live-verified retailer-hosted Google Merchant product XML feed URLs**.

Reconstructed XML, WooCommerce Store API endpoints, JSON product APIs, XML sitemaps, RSS/Atom feeds, search-only candidates, and transport-blocked candidates are excluded.

| Retailer | Native Google Merchant XML feed URL | Verification |
|---|---|---|
| Only SDD | https://onlyssd.com/?woocommerce_gpf=google | HTTP 200 + Google Merchant XML structure |

## Current coverage

- 32 WooCommerce retailers in the active matrix.
- 1 native retailer-hosted Google Merchant XML feed verified.
- 31 additional sites have no native feed URL verified by the current evidence set.
- No reconstructed product XML is included in this registry.

## Acceptance rule

A URL enters this registry only after a live response is received and the XML contains the Google Merchant namespace plus product-item fields including ID, title, link, price, availability, and condition. Sitemaps and generic RSS/Atom are explicitly rejected.

Source lineage: native-feed hunt workflow and strict merchant-feed validator.
