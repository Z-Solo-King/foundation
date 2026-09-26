# Repository Control Patterns

This document records lightweight repository-level controls learned from the
external `renderroute` fetcher repositories and reconciled with the Heroic AI
family architecture.

## Dynamic execution inputs

Workflows that execute a generic acquisition, benchmark, or maintenance job
should prefer runtime inputs or dispatch payloads over hard-coded target lists
when the target set is naturally dynamic.

Dynamic inputs MUST remain validated, bounded, and non-authoritative. They may
select work; they may not bypass policy, resource, security, provenance, or
deployment authorities.

## Workload isolation

Keep acquisition/execution, staging, ingestion, and downstream consumption as
separate steps with explicit handoff boundaries.

A successful acquisition may be preserved even when a downstream ingest or
secondary target fails. Failure reporting should identify the failed stage
without discarding independently valid outputs.

## Workflow safety defaults

Every non-trivial workflow should have:
- an explicit timeout;
- repository/job permissions limited to the scopes actually required;
- concurrency behavior chosen deliberately;
- deterministic failure classification where retries or fallback are used.

External event values must be treated as untrusted input and validated before
shell interpolation or privileged operations.

## Artifact and staging discipline

Generated artifacts must have explicit retention and provenance semantics.
Private or sensitive data must not be published through a public artifact path.

Cross-repository handoff must use the family's approved credential and bridge
authority. Introducing a second secret, token, staging authority, or deployment
path is prohibited.

## Failure-preserving execution

For multi-stage jobs, prefer:
1. execute;
2. persist valid partial outputs;
3. record structured failure state;
4. perform bounded recovery/fallback where policy permits;
5. fail the job when the requested acceptance condition is not met.

A green workflow is not equivalent to successful acquisition, runtime
acceptance, or production certification.

## Family-specific reconciliation

These patterns do not replace the canonical Heroic AI authorities:

- Foundation remains the public contract, GitHub Actions, and canonical
  deployment owner.
- Operations remains the private control plane and runtime authority.
- Production revision pins remain distinct from branch heads.
- L4 runtime evidence remains separate from source inspection and CI.
- Canonical cross-repository access continues to use the approved GitHub App path.

The purpose of this document is to keep reusable repository-control invariants
easy to discover without creating a competing policy authority.
