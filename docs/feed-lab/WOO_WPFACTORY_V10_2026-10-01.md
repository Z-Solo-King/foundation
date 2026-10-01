# WooCommerce WPFactory Family Recovery V10 — 2026-10-01

Source of truth: current main 1cabe0f0f8d5bc15788c24c68b1641b56a12a6f0 at branch creation.

Research-backed family addition:
WPFactory Product XML Feeds Manager for WooCommerce documents /products.xml as the default first-feed path. Additional-feed defaults are /products_2.xml and /products_3.xml, and a configurable subfolder example is /feeds/google.xml.

Recovery contract:
- one /products.xml representative per target;
- expand only after a stable non-empty XML-like 200 response;
- strict current same-host Google Merchant XML validation;
- retry 403/429/timeouts slowly and independently;
- public-only and no bypass/evasion;
- no Store API, plugin extraction or browser discovery;
- no random filename/token enumeration.

A family signal does not certify plugin identity, and transport-limited remains unverified.
