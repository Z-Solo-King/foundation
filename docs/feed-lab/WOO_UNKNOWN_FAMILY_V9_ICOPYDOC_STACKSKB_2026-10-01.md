# WooCommerce Feed Recovery V9 — iCopyDoc / StacksKB — 2026-10-01

V9 is a deterministic family-specific recovery probe derived from V8. It tests only the documented iCopyDoc feed-index paths:

- /wp-content/uploads/feed-xml-0.xml
- /wp-content/uploads/feed-xml-1.xml
- /wp-content/uploads/feed-xml-2.xml

Native certification remains strict: current HTTP 200, same host after redirect, XML/RSS/Atom-like, no challenge/access-denied, Google Merchant namespace, and g:id/g:title/g:link/g:price in one item/entry.

No random index/token enumeration, browser automation, authentication, or challenge bypass is permitted.
