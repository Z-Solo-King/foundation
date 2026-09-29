# Canonical Runtime Boundary

## Current topology

```
User
  -> Cloudflare Pages: ai
  -> Service Binding: HEROIC_BACKEND -> Worker: heroic
  -> Service Binding: OPERATIONS -> Worker: operations-edge
  -> Service Binding: CORE -> Worker: operations
  -> D1: research-intelligence
  -> Backblaze B2: artifacts/backups
```

## Authority

- Foundation owns the public contract, deterministic core, frontend, GitHub Actions and canonical release orchestration.
- Operations owns private chatbot orchestration, protected policy/resource governance, provider execution, private memory and promotion.
- Cloudflare is the runtime authority for deployed Worker versions, bindings, schedules and live resource state.
- D1 is the operational-state authority; B2 is artifact/backup storage.

## Public boundary

- `heroic` is the canonical backend Worker.
- The `heroic` workers.dev subdomain is disabled.
- No legacy `foundation` Worker is part of the production topology.
- No stale Pages project aliases are production authorities.
- `ai-cio.pages.dev` is the canonical public Pages front door.

## Release invariant

A release is valid only when the approved immutable Operations revision, current Foundation revision, Cloudflare bindings, protected policy values, D1 schema, deployment provenance and post-deployment runtime checks agree.

Do not infer production state from historical docs, branch names, or GitHub `main` position alone.
