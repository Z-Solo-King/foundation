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


## V18.1 execution update — 2026-10-01

- The three independent AI task families (extraction_assist, scan_triage, audit_assist) execute concurrently; provider fallback stays sequential inside each family.
- The canonical Operations rescue engine receives the exact V18 30-site registry at runtime.
- A bounded historical candidate lane now runs concurrently with browser and custom public recovery, harvesting same-host feed-like URLs from Wayback CDX and Common Crawl. These URLs remain hypotheses until the current retailer payload passes native Merchant XML validation.
- The historical lane is bounded by source-row and candidate-path limits and uses no authentication, cookie replay, CAPTCHA/challenge bypass, proxy rotation, or random-token enumeration.
- Legacy automatic feed workflows were deconflicted: the simple native-feed hunt and 9-site clean-recovery harness remain available only through manual dispatch and are not competing automatic authorities.
- The 32-site plugin fingerprint hunt remains a separate calibration surface; the V18 workflow is the canonical current recovery executor.
- No Cloudflare Worker was added for feed extraction. Cloudflare remains the application/control-plane runtime; feed recovery executes through the governed Foundation Actions surface with private Operations source material.

## Current truth

The V18 engineering pipeline is complete and reproducible on the current repository heads. A retailer is still not “native-feed verified” until a current payload satisfies the strict Google Merchant XML gate. Historical evidence, plugin fingerprints, Store API reconstruction, AI candidates, sitemaps, and archive records do not independently establish native-feed existence.
