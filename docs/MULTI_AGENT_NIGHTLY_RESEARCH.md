# Heroic AI Multi-Agent Nightly Research

Heroic AI is the product; nightly research is a bounded maintenance/learning capability behind it.

## Ownership
The private multi-agent implementation is owned by Operations under `private/multi_agent/`.

Foundation owns only the public workflow contract, artifact schema, deterministic baseline comparison, 24-program coverage assertions and GitHub Actions orchestration that fetches the approved private revision.

## Schedule and capacity
Three lanes run in parallel with eight programs each: 24 programs/night. Logical roles are capacity units rather than one job per role. Aggregate logical-agent capacity is bounded. The scheduled run has an explicit maintenance window and missing live executor configuration is a hard failure; no silent deterministic dry-run is acceptable.

## Execution bridge
Foundation obtains a short-lived GitHub App installation token, verifies the private Operations repository and exact immutable revision, checks out private source only under temporary runner storage, executes it on the public Foundation runner, and removes the private checkout/credentials in cleanup.

This is an execution bridge, not ownership transfer.

Privileged workflows do not execute pull-request code. Credential-bearing release/backup jobs are restricted to trusted `main` or approved manual dispatch, with third-party actions pinned.

## Public artifact boundary
Only the versioned public-safe nightly artifact crosses back into Foundation. Agent prompts, private notes, private topology, credentials and raw provider responses do not cross the boundary.

## Evidence
Lane artifacts are combined into a summary and compared with the prior successful baseline when available. Model findings remain candidate-only until the acquisition/evidence qualification path accepts them.

A nightly run is not authority for policy, security, billing, identity, resource limits or publication correctness.

## GitHub Actions execution policy
Foundation is the GitHub-hosted execution owner while private Operations workflows are intentionally absent. Future GitHub Actions capacity changes do not automatically authorize moving workloads into Operations; verify quota and make an explicit architecture decision first.

The bridge may dispatch only canonical Foundation workflows and may expose explicit dry-run/production-confirmation controls according to the workflow contract.

## Acceptance
The live 24-program run is an L3 acceptance gate. Repository source or a configured workflow is not evidence that the scheduled run actually executed successfully.
