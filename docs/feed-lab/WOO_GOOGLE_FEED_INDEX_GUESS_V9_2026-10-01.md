# WooCommerce Google Feed Index Guess V9 — 2026-10-01

V9 fixes the search-index transport bug found in V8. Search engines frequently wrap destination URLs (for example DuckDuckGo's uddg and Google's q/url parameters); V9 unwraps those before same-host filtering.

Search queries are expanded to filetype XML, Merchant namespace, g:price/g:id, XML/feed/google URL hints. The resulting URLs are re-probed against the current host.

The learned 10-family grammar matrix remains unchanged. This is still guess-only: no Store API, plugin extraction, page crawl, browser automation, authentication, challenge bypass, clearance-cookie replay, proxy rotation or random token enumeration.

Native acceptance is current same-host HTTP 200 XML with Google Merchant namespace plus g:id, g:title, g:link and g:price in one item/entry.