# WooCommerce Unknown 20 — Family Targeting Strategy — 2026-09-30

Current post-classifier family hypotheses:
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed
- Prime ABGB → WooCommerce Google Product Feed
- Variety Infotech → Google for WooCommerce / Google Listings & Ads

These are low-confidence hypotheses derived from concrete historical/plugin fingerprints. They are targets for verification, not final classifications.

The verifier is isolated from the full historical pass so changing the hypothesis set does not consume another full 20-site run.

WebToffee verification uses the family upload directory, documented/stable filename variants, discovered XML links, and same-host historical XML URLs.
WooCommerce Google Product Feed verification uses query and permalink forms and bounded partial-feed parameters.
Google for WooCommerce verification checks public GLA REST evidence and treats API integration separately from standalone XML.

Acceptance remains current-payload based: historical evidence may identify a family or URL, but only a current Google Merchant XML response is accepted as a native feed.