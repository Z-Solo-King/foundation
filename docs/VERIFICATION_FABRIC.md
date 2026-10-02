# Verification Fabric

The project uses a reusable deterministic verification fabric across Foundation and the private Operations repository.

## Crossfire model

Every verification plan carries six orthogonal lanes:
1. structure — ownership, topology, duplicate authorities, shadow surfaces
2. contract — schemas, APIs, types and compatibility boundaries
3. behavior — tests and deterministic runtime behavior
4. security — credentials, trust boundaries and adversarial cases
5. operational — budgets, retries, checkpoints, concurrency and provider/runtime reliability
6. reconciliation — cross-repository drift, documentation drift and workflow overlap

These are analysis roles, not six independent authorities. AI may be attached as advisory evidence, but it cannot promote itself into policy or product truth.

## Where it runs

The fabric runs on trusted pushes to main, every six hours, and manual dispatch. Because it reads the private Operations repository with a read-only GitHub App credential, it is a privileged audit workflow and intentionally does not run from untrusted pull-request code. Pull requests retain the existing required verification gates; the fabric provides additional cross-repository evidence on trusted revisions.

Operations remains free of GitHub Actions. Foundation remains the workflow authority.

## Shared family mechanics

Audit, Monitor and Extractor are treated as one mechanics family. Their domain policy remains separate, but deterministic mechanics are centralized where their semantics and correctness invariants are identical.

The shared kernel covers canonical evidence serialization, SHA-256 hashing, bounded numeric normalization, time parsing/freshness and related evidence primitives. Consumer modules retain their own authority, acceptance, acquisition, parsing and telemetry decisions.

This boundary is also used when the autonomous supervisor or verification fabric needs the same raw hashing mechanic. The refactor deliberately preserves existing digest byte-order semantics when replacing local hashing calls with the shared primitive.

## Promotion rules

Critical findings block the fabric. Warnings require review and produce evidence. The scanner never mutates credentials, protected policy, production releases, or Cloudflare configuration.

## Extraction relationship

The extractor-specific six-lane crossfire remains domain-specific. The project-wide fabric supplies the higher-level verification lanes around it. Extraction still uses explicit deterministic surface evidence: HTML, JSON-LD, embedded state, REST/GraphQL/XHR, sitemap/robots, feeds, pagination, variants, price/stock, images and browser escalation.

## Evolution rule

When a new capability is added:
- add its domain classification
- map it to an existing canonical workflow
- add at least one deterministic regression test
- add a documented owner/boundary
- avoid creating a new workflow when an existing workflow family can be extended


## Release-publication verification — 2026-10-02

The verification fabric treats GitHub Release publication as a privileged boundary. Feed outputs stay workflow artifacts, and release/tag publication primitives are rejected by deterministic policy before merge.
