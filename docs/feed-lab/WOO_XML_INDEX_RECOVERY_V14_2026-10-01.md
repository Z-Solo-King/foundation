# WooCommerce XML Index Recovery V14 — 2026-10-01

Only goal: current native Google Merchant XML URLs.

V14 fixes V13's overly restrictive archive queries. It retrieves a bounded set of historical URL records from Wayback and the current Common Crawl index, filters the returned URLs locally for XML/feed-like URLs, and revalidates those exact URLs against the current same host.

No URL filename generation, random token/index enumeration, Store API/product extraction, plugin inference, browser automation, authentication, bypass/evasion, or reconstructed XML.
