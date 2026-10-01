# Migration Live Evidence Checkpoint — 2026-10-01

This non-feed documentation change is a cross-repository runtime-validation checkpoint.

Current Foundation main before this change: `f43028ca6c6a4f4d3cecbfdb99ae4602330228b4`.
Current Operations main: `37b35ba9e94600d746bc81e48cd2918b0c239bc7`.
Canonical production Operations pin remains `90fa37df10d63824acd3fe20b64cc91043af9627`.

Operations #597 now has a private/local `mapper-runtime-evidence/v1` receipt for candidate `typescript-observation-contract-strict` at `47a18ac0112fdd3cc1f745b9f3a888a782f547ba`, against the exact Python reference pin `90fa37df10d63824acd3fe20b64cc91043af9627`.

Evidence result:
- frozen corpus: 32 cases
- exact differential: 32/32, zero mismatches
- normalized error taxonomy: pass
- security/policy/provenance invariants: pass
- cancellation/timeout: pass
- 3 benchmark repeats × 500 iterations
- p50/p95/p99, CPU, RSS, allocation and serialization data retained
- private read-only shadow: pass
- private read-only canary rehearsal: pass
- rollback/reference restoration: pass
- machine validator stage: `evidence_complete`
- authority promotion claim: false; Python remains canonical authority

A fresh Foundation hybrid run should now validate the repaired Operations current-head contracts:
1. generic extractor public `extract_products` / JSON-LD compatibility surface restored;
2. Browser Run adapter defers the platform-specific runtime import so plain Node tests do not resolve the `cloudflare:` module scheme.

This file intentionally changes no runtime authority, no production pin, no secrets, and no feed/WooCommerce behavior.
