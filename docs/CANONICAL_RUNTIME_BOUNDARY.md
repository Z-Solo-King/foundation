# Canonical Runtime Boundary

## Current topology

```
User
  -> Cloudflare Pages: ai
  -> Service Binding: HEROIC_BACKEND -> Worker: heroic (JavaScript edge)
  -> Service Binding: CORE -> Worker: heroic-core (Python application core)
  -> Service Binding: OPERATIONS -> Worker: operations-edge (JavaScript edge)
  -> Service Binding: CORE -> Worker: operations (Python control plane)
  -> D1: research-intelligence
  -> Backblaze B2: artifacts/backups
```

## Authority

- Foundation owns the public contract, deterministic core, frontend, GitHub Actions and canonical release orchestration.
- `heroic` is a thin native JavaScript ingress gateway.
- `heroic-core` retains the Python application/runtime implementation and its D1, artifact and Operations bindings.
- Operations owns private chatbot orchestration, protected policy/resource governance, provider execution, private memory and promotion.
- Cloudflare is the runtime authority for deployed Worker versions, bindings, schedules and live resource state.

## Transport rule

Worker-to-Worker transport uses Cloudflare Service Binding HTTP at language boundaries. Custom Python/JavaScript RPC is not required for the canonical transport path.

## Public boundary

- `heroic` is the canonical public backend Worker identity.
- The `heroic` workers.dev subdomain remains disabled.
- `ai-cio.pages.dev` remains the canonical public Pages front door.

## Release invariant

A release is valid only when the approved immutable Operations revision, current Foundation revision, Cloudflare bindings, protected policy values, D1 schema, deployment provenance and post-deployment runtime checks agree.

Do not infer production state from historical docs, branch names, or GitHub `main` position alone.