# Platform Access Cross-Fire Acceptance Matrix — 2026-10-02

This is the execution contract for the multi-provider chatbot test. The canonical access policy remains in Operations; Foundation owns the public workflow and safe evidence surface.

## Cross-fire model

Six independent analytical lanes are expected:

1. policy
2. access
3. extraction
4. evidence
5. countercheck
6. synthesis

The live provider benchmark executes concurrently against five or six configured providers. A provider can fail, be rate-limited, or be unavailable without making the platform itself unavailable.

## Source testing order

For each requested platform and evidence role:

1. official/documented API, feed or export
2. public HTML or public machine-readable representation
3. search-engine discovery of a specific public page
4. explicitly permitted first-party alternate representation
5. authorized browser/session continuation
6. independent alternate source family
7. PARTIAL/INACCESSIBLE with provenance

No challenge bypass, credential reuse, session-cookie harvesting, access-control circumvention, proxy rotation to evade blocks, unbounded crawling, or DRM circumvention is permitted.

## Completion definition

A green unit-test result means the routing contract is complete. A green live run means the configured provider fleet was actually reachable and produced deterministic contract-correct outputs. Neither result should be interpreted as universal real-time access to every platform.

The remaining runtime gate is live source qualification for platforms whose API, login, regional, dynamic, quota or policy state changes over time.
