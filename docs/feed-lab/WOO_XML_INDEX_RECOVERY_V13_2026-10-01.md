# WooCommerce XML Index Recovery V13 — 2026-10-01

Objective: recover actual current native Google Merchant XML URLs from historical public indexes only.

Sources:
- Wayback CDX records whose archived MIME type is application/xml.
- Common Crawl index records for URLs matching .xml.

Each historical URL is current-revalidated against the same host. Only the current payload can pass native Merchant validation.

No filename generation, random token enumeration, Store API/product extraction, plugin inference, browser automation, authentication, challenge bypass, proxy rotation or reconstructed XML is used.
