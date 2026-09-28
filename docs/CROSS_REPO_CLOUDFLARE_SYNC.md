# Cross-repo + Cloudflare synchronization record

Snapshot: 2026-09-28 (Asia/Kolkata)
Purpose: compact bridge between the public Foundation repository, private Operations repository, GitHub Issues/PRs, and live Cloudflare state.

## Authority model
- GitHub main trees are the repository source of truth.
- Fresh GitHub Issues/PRs and current CI are live queue/evidence.
- Cloudflare live API state is the source of truth for deployed Workers, D1, schedules, bindings and production configuration.
- Dated audit/handoff documents are historical evidence unless explicitly marked current.
- This file is a synchronization index, not a replacement for security, deployment or runtime contracts.

## Live GitHub state observed
- Foundation main: c79db910b0808eee59a3c1f0e23dfe06db33241b
- Operations main: 44bbbd3567ac9f41c1ff63e3f5f295d4491c0a00
- Foundation open issues: #1249, #1247, #157, #58.
- Foundation open PRs: #1439, #1427.
- Operations open issues observed: #1103, #1066, #1027, #603, #597, #145.
- Operations had no open PRs in the inventory pass.

## Cross-fire validation
Two independent lenses must agree before a state is treated as current:
1. Repository lens: code/config/docs, issue/PR state, current branch SHA.
2. Runtime lens: Cloudflare Worker/D1/API state and deployment provenance.

A GitHub document never certifies a Cloudflare deployment by itself. A Cloudflare deployment never replaces the repository contract.

## Public-safe Cloudflare mapping
The public repository may document only the public-safe Worker/deployment relationship. The live account inventory currently includes the public-facing foundation and heroic Workers; their exact runtime configuration remains a Cloudflare/runtime concern.

The private Operations synchronization record contains the complete live Worker inventory and D1 identity. Do not copy private bindings, credentials, secret names/values, or private runtime policy into this public repository.

## Documentation compression rules
Retain:
- canonical current-state/ownership/security/deployment contracts;
- active issue acceptance criteria;
- runtime evidence required to reproduce or audit a decision;
- substantive historical findings that explain current architecture;
- machine-readable schemas and manifests consumed by automation.

Compress or retire:
- one-line dated status stubs whose only purpose is pointing to a canonical document;
- superseded snapshots that contain no unique evidence;
- duplicate policy documents when one canonical owner exists;
- repeated chat/session notes after their durable decisions have been transferred.

Never delete substantive historical evidence merely because it is old; classify it as historical and link it from the relevant index.

## Current cleanup decisions
- The public HYBRID_MIGRATION_STATUS_2026-09-28.json is a pointer-only stub and is removed from active documentation; the authoritative migration state remains in Operations.
- The substantive multi-language scan remains retained as historical evidence.
- No Cloudflare production resource is deleted by this documentation cleanup.
