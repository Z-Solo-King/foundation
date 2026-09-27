# Issue #1247 — WooCommerce Google Feed Recovery

Date: 2026-09-27

## Current-head continuation

This implementation is rebased onto the current Foundation `main` head rather than merging the stale 2026-09-26 audit branch wholesale.

### Scope

Only the nine unresolved retailers from #1247 are targeted:

- ithunt
- kccomputers
- KRG KART
- PC Kumar Infotech
- PCHubShop
- SCL Gaming
- Variety Infotech
- Moskeys
- Theproaudio

### Recovery surfaces

The job uses only public/unauthenticated surfaces:

- native Google Merchant feed URL candidates
- public WooCommerce Store API aliases
- adaptive public pagination
- normal HTTP transport
- curl JSON fallback

A Store API reconstruction is recorded separately from a native feed and is never mislabeled as the retailer's native Google Merchant feed.

### Safety and classification

HTTP 403/429/challenge responses remain transport-unverified. The implementation does not attempt CAPTCHA solving, Cloudflare challenge bypass, authentication bypass, proxy evasion, clearance-cookie replay, or stealth anti-bot behavior.

### Fix included

The inherited rescue tool referenced `execFileAsync` without defining it. The current-head version explicitly imports `execFile` and `promisify` and defines the fallback correctly.

### Verification boundary

This PR provides the current-head recovery machinery and evidence workflow. Actual feed recovery remains determined by the public execution result and uploaded artifact.
