# GitHub Project Handoff — 2026-09-21

> Foundation mirror. This handoff is intentionally mirrored so a future GitHub-only chat can start from either repository.

## Canonical repository state

- Foundation `main`: `0e5e3532e91ea40040b718a8dcbf7e3f66919d30`
- Operations `main`: `a03c90fde14ccf89535020f50a5e15e51123c1b3`
- This is the canonical GitHub-side handoff for the next AI/chat session.
- Cloudflare/live runtime verification remains separate from this GitHub-only context.

## Latest merged Operations work

- #707 / `3c4fad5f...`: endpoint-discovery security/parity hardening and frozen 32-case corpus.
- #708 / `acfd0e9c...`: polyglot registry, placement contract, documentation ownership cleanup and duplicate adapter retirement.
- #709 / `d3c680ce...`: acquisition IP allow-listing, streaming POST bounds, scoped task-envelope signing keys, provider-error preservation and production test-double removal.
- #710 / `4a471024...`: DNS revalidation immediately before public acquisition to close the hostname rebinding window.

## Current concrete implementation blocker

### #711 — DurableResourceLedger reservation orphan

This is now the highest-priority concrete code defect.

Observed failure:
- an over-limit reservation can leave an uncharged `reserved` row;
- later release/reconcile can subtract quota that was never charged;
- quota can therefore under-count active reservations and permit an over-limit state.

Proposed direction already recorded in #711:
- make finalization conditional on proof that the reservation charge changed one row;
- distinguish idempotent replay from identity mismatch;
- delete failed pending state deterministically;
- fix the D1 fake commit behavior;
- add orphan/reconcile and quota-invariant regression coverage;
- verify real/preview D1 `changes()` semantics and a concurrent over-limit probe.

Do not close #711 from static inspection alone.

## Remaining runtime/evidence gates

The older acceptance backlog remains intentionally open:
- #119 memory/provenance/version-boundary evidence;
- #132 task-envelope replay across real version boundary;
- #145 maintenance receipt;
- #197 live conversational execution/idempotency/policy denial;
- #340 provider streaming interruption/reconciliation;
- #352 representative extractor/mapper runtime replay;
- #385 cross-surface restart/recovery;
- #597 mapper migration evidence ladder;
- #603 portability/shadow/canary/rollback evidence.

These are evidence gates, not reasons to create duplicate implementations.

## Migration state

The repository-side polyglot migration work is complete at the implementation/evidence rung:
- Rust candidates: URL identity, text normalization, HTML/product-card, JSON-LD, Link-header pagination, robots/sitemap.
- TypeScript candidates: search/provider adapters, browser acquisition, public endpoint discovery, Next.js product-state, acquisition planner, edge-worker.
- Go: bounded HTTP fan-out benchmark/pilot.

Python remains the protected authority for policy, governance, persistence, replay/idempotency, provenance and rollback-sensitive semantics.

## Documentation/ownership

- `polyglot/REGISTRY.json` is the machine-readable candidate inventory.
- `docs/CODE_OWNERSHIP_AND_PLACEMENT.md` is the placement contract.
- `docs/CURRENT_SOURCE_OF_TRUTH.md` is stable state/ownership guidance, not a historical release log.
- Foundation owns public-safe common standards; Operations keeps only private addenda.

## New-chat procedure

Read this file first, then:
1. inspect both repos' current `main` SHAs;
2. inspect open PRs;
3. inspect #711 and its proposed fix before touching the acceptance backlog;
4. inspect the Foundation hardening PR/branch;
5. keep repository implementation work separate from live Cloudflare/runtime acceptance.

## Latest active implementation queue discovered after the prior handoff

- **#712** — open PR implementing the #711 DurableResourceLedger orphan-reservation fix. Review and required tests first; #711 stays open until Python 3.14/full-suite and real/preview D1 `changes()` evidence are recorded.
- **#717** — task-envelope/replay guard correctness and fail-closed behavior.
- **#718** — Worker/chat auth-before-parse, body limits, exception leakage, requested_fields typing, provenance, routing and decomposition.
- **#719** — reconciliation poison-row isolation, post-reserve deadline release, resource-kind reservation mapping, and invariants.
- **#720** — protected-policy no-op enforcement and semantic policy digest.
- **#721** — SSE terminal-state vocabulary, including `NOT_ATTEMPTED` and unknown-state fail-closed handling.

These are newer concrete implementation findings and must be reviewed before treating the older runtime acceptance backlog as the only remaining work.
