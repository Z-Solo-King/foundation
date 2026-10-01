# WooCommerce Native XML Recovery V18 — Foundation Execution

Date: 2026-10-01

## Ownership

- **Foundation** owns hosted GitHub Actions execution.
- **Operations** owns the private feed-recovery implementation and the 30-site learning registry.
- The workflow consumes an immutable Operations commit through the existing read-only GitHub App boundary.
- Operations does not host a competing GitHub Actions workflow for this recovery.

## Evidence lanes

1. governed AI candidate generation;
2. public browser/network observation;
3. public custom/API recovery;
4. canonical rate-aware rescue;
5. deterministic native Google Merchant XML validation.

AI-generated URLs are hypotheses only. Browser/API observations are evidence about acquisition surfaces, not automatic feed certification.

## Native-feed acceptance

A result is certified as a native Google Merchant XML feed only when the current payload passes the canonical Google Merchant validator. Store API reconstruction, sitemap/XML discovery, historical references, plugin fingerprints, and generated XML are not native-feed certification.

## Safety boundary

The recovery is public read-only and does not:

- inject retailer credentials;
- replay clearance cookies;
- solve CAPTCHA or Cloudflare challenges;
- rotate proxies for evasion;
- issue state-changing requests;
- convert Store API output into a native Merchant feed.

## Current completion boundary

The engineering path is complete and reproducible. The recovery issue remains evidence-open until a current target produces a payload that passes the native-feed validator. Transport-blocked and unverified targets remain distinct from feed absence.

## Related surfaces

- Operations V18 registry: `data/feed_lab/woocommerce_30_registry_v18.json`
- Foundation workflow: `.github/workflows/woocommerce-native-xml-recovery-v18.yml`
- Authority registry: `docs/WORKFLOW_AUTHORITY_REGISTRY.json`
- Canonical recovery implementation: `operations/private/feed_recovery/`
