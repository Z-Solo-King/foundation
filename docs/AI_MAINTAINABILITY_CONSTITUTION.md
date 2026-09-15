# AI Maintainability Constitution

This document is the public-repository subset of the project maintainability rules. It is normative for humans and coding agents.

## Ownership

Foundation owns public-safe deterministic research contracts and algorithms. Operations owns private control, memory, provider policy, protected security/billing/access authority, and private credentials.

## Module discipline

New non-trivial modules explain purpose, ownership, inputs/outputs, failure semantics, and maintenance/deprecation path. Pure logic is separated from transport and persistence. Workers and API handlers remain thin.

## Token-efficient navigation

Agents read `AI_NAVIGATION_INDEX.json` first, then the specific canonical entrypoint, then tests. They do not scan the whole repository unless the task requires cross-cutting analysis.

## Evidence discipline

Unknown, inaccessible, contradictory, stale, partial and inferred states remain distinct. Deterministic extraction observes evidence; mapping/authority rules decide canonicality; synthesis must not fabricate missing evidence.

## Boundary discipline

Foundation never imports private Operations implementation details. Public contracts can be consumed by Operations, but private memory/policy/credentials never become Foundation-owned runtime state.

## Cleanup

Unclassified legacy/dead code is not acceptable. Code is active, compatibility-retained, archived with provenance, or scheduled for deletion. Tests and migration/rollback consumers must be checked before removal.

## Validation

Use the cheapest deterministic validation first, then broader evaluation. Passing tests does not imply production certification; production-shaped evidence is tracked separately.
