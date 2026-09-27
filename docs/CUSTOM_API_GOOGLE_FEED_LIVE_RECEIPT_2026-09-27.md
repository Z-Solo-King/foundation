# Custom/API Google Feed Recovery — 2026-09-27 live receipt

Issue: #1249

## Authoritative execution

GitHub Actions run **36294460678** (`Custom API Google Feed Recovery 1249 Live`) completed successfully on commit **4d20081f2ec6b31b6b32443c62317da1c088285f**.

The run executed two live phases on a public `ubuntu-latest` runner:

1. Deterministic HTTP discovery across 13 unresolved retailers.
2. Headless Chromium network discovery across apex/www/API roots.

Artifact: **10923472353** (`custom-api-google-feed-1249-live`).

## Result

**0 new Google Merchant XML feeds verified.**

Strict validation required an actual XML/RSS/Atom payload containing the Google Merchant namespace (`http://base.google.com/ns/1.0`), product item/entry nodes, and populated Google Merchant fields. JSON catalogs, ordinary sitemaps, analytics endpoints, and HTML pages were not counted.

## Live transport state

| Retailer | Current runner observation |
|---|---|
| BuildMyPC | Homepage 429 on apex and www; transport-unverified |
| Easy Shoppi | Homepage 200; Next.js public session/API activity observed; no Merchant XML |
| Fingers | Homepage 200; public `/secure/api/services/*` JSON activity observed; no Merchant XML |
| LebyoPC | Homepage 403 on apex and www; transport-unverified |
| ArcadeX | Homepage 200; Next.js public session/API activity observed; no Merchant XML |
| altf4gear | Homepage 200; public cart/analytics API activity observed; no Merchant XML |
| Logtech | Homepage 200; cart JSON endpoint observed; no Merchant XML |
| DigiBuggy | Homepage 200; storefront loads; no Merchant XML observed |
| TheValueStore | Homepage 200; public `/api/x3/*` JSON endpoints observed; no Merchant XML |
| Furtados | Homepage 200; Magento GraphQL product/category traffic observed; no Merchant XML |
| KeySync | Homepage 200; separate API host observed; no Merchant XML |
| The Rhythm House | Homepage 200; Dotshowroom API traffic observed; no Merchant XML |
| CloudTechAsia | Homepage 200; Hyperinvento API/product traffic observed; no Merchant XML |

## Newly captured platform fingerprints

- **Fingers:** `https://www.fingers.co.in/secure/api/services/...` JSON endpoints.
- **TheValueStore:** `https://thevaluestore.in/api/x3/...` JSON endpoints.
- **Furtados:** `https://www.furtadosonline.com/graphql?...` Magento GraphQL product/category requests.
- **The Rhythm House:** `https://api.dotshowroom.in/api/dotk/vo1/...` storefront APIs.
- **CloudTechAsia:** `https://api.hyperinvento.com/v1/consumer/sellers/.../products?...` and `https://api.hyperinvento.com/v3/admin/sales_channel_index/?domain=https://cloudtechasia.in...`.
- **KeySync:** `https://api.keysync.co/...` is a separate public API host.

These are catalog/API surfaces, not Google Merchant feeds. They are preserved as discovery inputs for future platform-aware feed lookup.

## Evidence boundary

BuildMyPC 429 and LebyoPC 403 remain **transport-unverified** and are not classified as feed-negative.

No CAPTCHA, Cloudflare challenge, authentication, clearance-cookie replay, proxy rotation, or anti-bot evasion was used.

Current repository-side disposition: **complete for the reusable live-discovery/validation tooling**.

Issue #1249 remains open because a real Google Merchant XML feed has not been independently verified for the remaining 13 retailers; external/hidden feed evidence is still required.