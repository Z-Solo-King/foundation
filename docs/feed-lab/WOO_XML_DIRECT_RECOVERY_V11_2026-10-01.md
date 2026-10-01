# WooCommerce XML Direct Recovery V11 — 2026-10-01

Objective: recover an actual current public Google Merchant XML URL from the 30-site learning corpus.

This runner does only XML URL discovery and current XML validation. Sources are:
1. explicit XML/feed URLs referenced in current homepage/robots/sitemap surfaces;
2. search-index URLs from Google/Bing/DuckDuckGo;
3. exact current same-host URL references harvested from those public sources.

It never treats a sitemap itself, WordPress RSS, Store API, generic API, reconstructed XML, historical-only URL, or challenge page as a feed.

Native acceptance is strict: current HTTP 200, same host after redirect, XML/RSS/Atom-like, no challenge/access denied, Google Merchant namespace, and g:id/g:title/g:link/g:price inside the same item/entry.

No plugin inference, Store API, product extraction, browser automation, authentication, bypass/evasion, proxy rotation, or random-token enumeration.
