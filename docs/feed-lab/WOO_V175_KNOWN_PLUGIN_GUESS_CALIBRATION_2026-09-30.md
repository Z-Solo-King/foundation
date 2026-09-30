# WooCommerce Known-Plugin Guess Calibration — 2026-09-30

## Purpose

The previous ten known/excluded WooCommerce sites are now included in a dedicated guessing/calibration cohort. They remain outside the active 21-site production denominator.

Calibration sites:

PC Studio, Quickin Computers, Avikaretails, Geekbees, Ninja Dog, Network IT Store, My Nexus Infosys, Solanki Enterprises, Only SSD, IT Gadgets Online.

These sites are useful because the repository already has historical endpoint/platform knowledge for several of them, including WooCommerce Store API mode; the calibration job deliberately tests feed-plugin URL hypotheses separately rather than treating Store API knowledge as a feed proof.

## Cross-fire execution

Each site runs four independent public-only lanes concurrently:

1. Fixed plugin paths: WooCommerce Google Product Feed, CTX Feed, AdTribes, WPPFM, WebToffee, CodeSolz and FeedCraft.
2. Public output-directory indexes for generated/random feed filenames.
3. Public HTML/robots/sitemap references.
4. Wayback feed-like URL hints followed by current validation.

GitHub Actions runs all ten site jobs independently with fail-fast disabled.

## Acceptance

A hit is only recorded when the current response is same-host and passes the strict Google Merchant XML validator. A sitemap, Store API, normal RSS/Atom, historical-only result, or guessed filename without a valid current payload is not promoted.

## Why this matters for the active 21-site hunt

The calibration cohort can reveal which feed-plugin families and URL patterns are actually observable in the wild. Those observations can then improve candidate ordering for the unresolved active sites without contaminating their production acceptance counts.

The active V175 architecture already separates browser/XHR discovery, transport/provenance and bounded public-only acquisition. fileciteturn632file0L7-L9