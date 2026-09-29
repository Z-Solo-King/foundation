# Public Feed Recovery — Issue #1247

Date: 2026-09-29

## Scope

Issue #1247 covers the WooCommerce-specific Google Merchant feed recovery lane. The broader 32-site package was also exercised; the current unresolved native-feed set is the 10 retailers recorded in the issue history.

## Acceptance contract

A URL is promoted to **native Google Merchant feed** only after the live payload itself validates as a supported Google Merchant XML product source. Google documents RSS and Atom XML formats, with the Google Merchant namespace and required product attributes. Generic RSS/Atom, XML sitemaps, HTML, ordinary WooCommerce APIs, and reconstructed snapshots are not native-feed evidence.

WooCommerce's official Google Product Feed extension documents the canonical `?woocommerce_gpf=google` endpoint and partial-feed parameters such as `gpf_start` / `gpf_limit`. WooCommerce also documents that its Google integration can synchronize through the API rather than exposing a traditional public XML feed.

## Completed development

The recovery implementation has exercised, where publicly available:

- canonical WooCommerce Google Product Feed URL families;
- plugin-specific feed families for CTX/FeedCraft, Product Feed PRO/WPFM and Codesolz;
- generated/public upload-directory discovery;
- robots.txt, XML sitemap and homepage/source discovery;
- explicit feed URLs exposed in HTML/JavaScript/configuration;
- normal same-site browser session warmup and cookie reuse;
- Chromium browser retrieval and public XHR/network-response observation;
- Common Crawl and Wayback historical URL discovery;
- direct HTTP and curl fallback;
- multiple GitHub-hosted runner operating systems;
- strict payload validation with transport/provenance classification.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, proxy-rotation evasion, or stealth anti-bot mechanism is part of the implementation.

## Current evidence

- The broader 32-site native-feed pass verified **1/32** retailer-hosted native Google Merchant XML feeds: Only SDD.
- The focused unresolved set has **no additional verified native feed** after the permitted public discovery passes.
- Reconstructed Store API XML snapshots, where available, are retained as separate fallback evidence and are never promoted as native retailer feeds.
- HTTP 401/403/429, challenge pages, DNS/transport failure, or geographic denial remain **transport-unverified**, not proof that a retailer has no feed.

## Current blocker

The remaining gap is legitimate acquisition access to the unresolved retailers, not another generic candidate-path sweep. Recent focused testing found GitHub-hosted runner 403/access-denied responses for several retailers, while the configured Cloudflare Browser Run credential returned authorization/rate-limit errors during fallback testing. Historical/index discovery did not surface additional validated native feeds.

Therefore:

1. **Extractor development:** complete for the currently permitted public discovery surface.
2. **Evidence/validation:** complete for the executed passes.
3. **Native-feed recovery:** remains externally blocked/unverified for the unresolved retailers.
4. **Next productive action:** use an authorized acquisition surface/egress or retailer-provided/publicly reachable feed URL; do not add anti-bot bypass logic.

## Cloudflare role

Cloudflare Browser Run is technically suitable for normal browser-based acquisition and network observation, but it is not a substitute for authorization. Current project evidence shows the configured Browser Run credential is not currently usable for this recovery lane. No Cloudflare production change is required to declare the extractor implementation complete.

## Research references

- Google Merchant Center XML product-file guidance: RSS 2.0 and Atom 1.0.
- WooCommerce Google Product Feed documentation and feed-generation options.
- WooCommerce REST API documentation, which confirms ordinary product APIs are product-data APIs rather than proof of a retailer-hosted Merchant feed.

The repository deliberately keeps the distinction between **native feed**, **reconstructed snapshot**, and **transport-unverified** evidence.
