# GitHub Project Handoff — 2026-09-21

## Canonical repository state

- Foundation `main`: `0e5e3532e91ea40040b718a8dcbf7e3f66919d30`
- Operations `main`: `4a471024c2885c3167d1ec9b4b3c648b9e324e7e`
- Cloudflare configuration is intentionally **not modified from this GitHub-only handoff**; live runtime evidence remains a separate acceptance surface.
- GitHub Actions remains the sole Foundation production deployment authority. Cloudflare Workers Builds and Deploy Hooks remain out of scope for GitHub-side changes.

## Work completed in this migration/scan wave

### Operations
- #707 merged: public endpoint discovery hardening and 32-case corpus.
- #708 merged: canonical polyglot placement, registry and documentation ownership cleanup.
- #709 merged: acquisition IP policy, streaming POST bounds, scoped task signing keys, provider-error preservation, removal of production test-double fallback.
- #710 merged: DNS rebinding revalidation immediately before public acquisition.
- Current Operations head: `4a471024...`.

### Foundation-side hardening branch
Branch: `fix/newer-security-coverage-workflows`

Prepared but not yet merged:
- public acquisition global-IP allow-list and provider denylist;
- scoped public cursor key derivation;
- truthful failed-run persistence logging;
- full B2 artifact persistence coverage;
- Worker-enforced CSP/security response headers;
- narrower frontend `connect-src`;
- retirement of superseded nightly v3/v4 workflow files;
- explicit timeout/concurrency controls across the affected workflows;
- retirement of obsolete push-probe workflows;
- retirement of duplicate `edge_ts/` and `shadow/edge-ts/` copies in favor of `polyglot/edge-worker/`;
- canonical Operations pin advanced to `4a471024c2885c3167d1ec9b4b3c648b9e324e7e`;
- workflow-policy tests updated to enforce the new contract.

## New blocker discovered after the earlier scan

Operations #711 is a concrete FIX_NOW defect in `DurableResourceLedger.reserve()`:
- over-limit reservation can leave an uncharged `reserved` row;
- later release/reconciliation can under-count active reservations;
- repository tests reportedly disagree with current behavior;
- required evidence includes Python 3.14 test green plus real/preview D1 batch `changes()` semantics and a concurrent over-limit probe.

Do not close #711 from source inspection alone.

## Remaining intentional acceptance gates

These are not being manufactured into implementation issues:
- Foundation #157 — one real 24-program nightly execution with retained artifacts.
- Foundation #452 — real client disconnect/cancellation evidence for the public SSE lifecycle.
- Operations #119/#132/#145/#197/#340/#352/#385/#597/#603 — live runtime/control-plane/evidence gates documented in their issue bodies.
- Operations #711 — active implementation/security defect requiring a dedicated fix.

## Migration authority policy

Python remains authoritative for policy, governance, persistence, replay/idempotency, provenance and rollback-sensitive semantics until the full evidence ladder is satisfied.

Polyglot candidates remain candidate/shadow/evidence surfaces unless their issue/candidate record explicitly documents authority promotion.

## New-chat startup procedure

1. Read this handoff file.
2. Read `docs/CURRENT_SOURCE_OF_TRUTH.md` and `REPOSITORY_MAP.json`.
3. Check Foundation `main`, Operations `main`, open PRs and the newest issues.
4. Treat Operations #711 as the current concrete FIX_NOW item.
5. Treat the Foundation hardening branch/PR as repository-side cleanup pending protected checks.
6. Do not reopen or duplicate older runtime-gated issues simply because their evidence is still absent.
7. Keep GitHub and Cloudflare verification separate unless the appropriate connector is available.
