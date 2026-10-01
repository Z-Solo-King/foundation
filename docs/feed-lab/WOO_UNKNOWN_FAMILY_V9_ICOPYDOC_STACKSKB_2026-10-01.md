# WooCommerce Feed Recovery V9 — iCopyDoc / StacksKB — 2026-10-01

V9 used only documented iCopyDoc feed-index grammar.

Probes:
- /wp-content/uploads/feed-xml-0.xml -> HTTP 200, same host, application/xml, empty payload
- /wp-content/uploads/feed-xml-1.xml -> HTTP 404
- /wp-content/uploads/feed-xml-2.xml -> HTTP 404

Native Merchant validation:
- 0 verified URLs
- no Google Merchant namespace / item payload was present

Interpretation:
- The iCopyDoc family grammar is independently corroborated.
- StacksKB currently exposes an empty feed-xml-0.xml placeholder/file, but no populated native Merchant XML feed was recovered.
- The documented additional feed indices do not exist currently.
- This is not proof that the plugin is absent; it is current public endpoint evidence only.

V9 is therefore a terminal result for this iCopyDoc hypothesis unless new public evidence appears. Do not broaden into arbitrary feed-index enumeration or return to the cross-family guessing matrix.
