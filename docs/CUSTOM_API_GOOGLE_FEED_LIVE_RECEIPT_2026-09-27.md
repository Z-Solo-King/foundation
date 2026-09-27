# Public Feed Recovery Methodology — Issue #1249

Date: 2026-09-27

The public Foundation repository retains the generic discovery and validation methodology. Live target identities, API hosts, request paths and raw network observations are maintained on the private Operations surface.

## Method

The private execution path combines deterministic HTTP discovery with headless-browser network observation. Candidate XML is counted only when it contains the Google Merchant namespace, product item/entry nodes and populated merchant fields.

Ordinary JSON APIs, HTML pages, generic sitemaps and analytics traffic are not classified as Google Merchant XML feeds.

## Safety

Transport blocks such as HTTP 403/429 and challenge pages remain unverified rather than being treated as feed-negative. No CAPTCHA solving, challenge bypass, authentication bypass, proxy rotation or clearance-cookie replay is permitted.

## Evidence boundary

The public mirror intentionally contains no live retailer names, target URLs, API hostnames or run/artifact identifiers. Actual feed verification remains a private evidence task.
