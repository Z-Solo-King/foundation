---
applyTo: "backend/**/*.py"
---

# Backend AI maintenance contract

- Read `AI_CODEMAP.json` before editing and identify the canonical owner.
- Foundation owns public-safe contracts, evidence/intelligence primitives, deterministic planning, and the public API boundary.
- Do not add private provider policy, secrets, heavy extraction, or heavy product mapping here.
- Prefer the smallest change that preserves the typed contract and explicit uncertainty/contradiction states.
- Reuse an existing contract/model before adding a new DTO or policy.
- Keep functions cohesive and bounded; split only at a stable responsibility boundary.
- Add focused branch coverage for each behavior change; do not grow catch-all coverage files just to raise the percentage.
- Do not translate network failures into successful empty results.
