# Heroic AI — Foundation

Public application contract and deterministic core for **Heroic AI**, the chatbot-first research assistant.

Heroic AI is the product. Research is one of its capabilities, not a separate product. Foundation owns the public-safe request/evidence contracts, deterministic research primitives, public frontend boundary, and canonical public deployment path. Operations owns private chatbot orchestration, protected policy/resource authority, private memory, model/provider execution and promotion.

## Read first

1. `docs/HEROIC_AI_PRODUCT.md`
2. `README.md`
3. `docs/DOCUMENTATION_INDEX.md`
4. `REPOSITORY_MAP.json`
5. `docs/FAMILY_CONTRACT.json`
6. `docs/FAMILY_ARCHITECTURE.md`

Live repository state and fresh GitHub evidence override dated continuity notes.


## Current AI engineering architecture — September 2026

The canonical public entrypoint is the Cloudflare Pages project `ai` at the assigned hostname `https://ai-cio.pages.dev`. Its backend Worker identity is `heroic`; private chatbot/provider execution remains in Operations through the `FOUNDATION`/service-binding boundary.

The project is strict-$0 by policy. Provider selection is runtime-aware and fail-closed on unknown billing/quota state. The current provider-control policy is documented in Operations at `docs/AI_PROVIDER_CONTROL_POLICY_2026-09-25.md`. GitHub Models is retired and is not a provider path.

GitHub Actions in Foundation remains the canonical deployment owner. External AI coding tools are developer-side lanes; they are not deployment or policy authorities.

## Heroic AI product boundary

```text
User
  -> Heroic AI frontend
  -> authenticated public chat/research contract
  -> private Operations control plane
  -> deterministic tools / evidence / approved model execution
  -> grounded response + citations + state + artifacts
```

The frontend must never become a second authority. Private policy, memory, provider secrets, resource governance and promotion remain in Operations. Public research/evidence semantics remain in Foundation.

## Public capabilities

- conversational chat contract and lifecycle boundary;
- research runs and evidence-backed answers;
- deterministic extraction/mapping/normalization;
- citations, uncertainty and provenance contracts;
- files/artifacts and research workspace UI;
- public health/readiness and canonical production deployment.

## Deterministic core

`foundation_core/` is the canonical public implementation for deterministic observed-data routing, normalization, plausibility checks and product mapping. Operations consumes it through the declared public boundary and does not copy its implementation authority.

## Storage and backup boundary

D1 is used for compact operational state. Backblaze B2 is the artifact/object-storage path. The former R2 design is retired.

The canonical repository-backup workflow is `.github/workflows/b2-repository-backup.yml`. It mirrors both `foundation` and private `operations` to B2, uses the purpose-specific GitHub App (`OPERATIONS_APP_ID`/`OPERATIONS_APP_PRIVATE_KEY`) for private Operations repository access, uses the separate B2 credentials for storage access, verifies uploaded metadata/SHA-256 integrity, and performs archive extraction plus Git integrity checks from the remote B2 objects. A successful workflow execution is required before claiming live backup/restore health; repository source inspection alone is not production backup evidence.
