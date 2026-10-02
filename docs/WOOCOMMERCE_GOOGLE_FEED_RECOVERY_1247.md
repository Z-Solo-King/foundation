# Public Feed Recovery Methodology — Issue #1247

Date: 2026-10-02

The public Foundation repository retains methodology and public contracts only. Live retailer identities, target URLs, AI-discovered candidate paths, raw responses, credentials and recovery output are maintained on the private Operations surface.

## Method

Recovery candidates may use public native Google Merchant feed paths, public WooCommerce Store API surfaces, adaptive pagination and bounded HTTP/curl fallback.

A result is considered a native Google Merchant feed only when the response contains the Google Merchant namespace plus product item/entry nodes and required merchant fields.

A Store API reconstruction is recorded separately and is never presented as the retailer's native Merchant feed.

## Acquisition boundary

The public repository defines candidate-generation and evidence semantics only. Live acquisition, browser/network retrieval, target registries, adaptive retry, provider-assisted hypothesis generation and retailer-specific recovery logic belong to Operations.

A transport failure is not a feed-negative result; the selected route and resulting evidence must be recorded.

## AI / Cross-Fire boundary

AI may generate candidate feed hypotheses in independent Cross-Fire lanes. Those lanes are candidate-only and must not claim that a path exists. Deterministic live retrieval and feed validation remain authoritative.

## Evidence boundary

The public repository does not contain the live target registry or target-specific recovery output. Actual recovery remains an evidence-gated private execution task.

## Migration ownership gate — 2026-10-02

- **Foundation:** public feed methodology, contracts, validation semantics and safe orchestration metadata only.
- **Operations:** live retailer registry, acquisition/extraction execution, provider-assisted candidate generation, target-specific recovery state and production recovery authority.
- **CrossFire:** independent AI lanes may propose hypotheses, but deterministic retrieval/validation remains the acceptance authority.
- **Status discipline:** unresolved targets remain open or evidence-gated until current execution evidence satisfies their written acceptance criteria; historical receipts are never reused as closure evidence.


## Distribution safety rule — 2026-10-02

Recovery output is an evidence artifact, not a public GitHub Release. The Foundation workflow surface must not create or upload GitHub Release assets for feed recovery, and generated indexes must not point to release download URLs. Any accidental wc-google-feed-latest release/tag is treated as invalid state and removed by the governance control.
