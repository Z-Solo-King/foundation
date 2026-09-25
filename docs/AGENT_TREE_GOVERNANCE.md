# Governed Agent Tree

Status: proposed implementation on branch `agent-tree-governance-2026-09-25`.

## Purpose

Use a small, evidence-driven delegation tree for development work without creating competing authorities or requiring every task to be delegated.

```text
Main session (high effort)
  ├─ Explorer (opus, medium): read-only code and architecture discovery
  ├─ Worker (opus, medium): scoped implementation and focused tests
  └─ Researcher (opus, medium): documentation and external evidence lookup

Advisor: on-call review gate before major plans, after a repeated error,
and before declaring a long task complete.
```

## Role contracts

### Explorer

- Read code, contracts, tests, workflows, issues, PRs, and exact file ownership.
- Return findings with paths, revisions, risks, and the first missing acceptance rung.
- Do not modify files, change issue state, or declare a fix complete.

### Worker

- Implement one authorized, non-overlapping slice from current `main`.
- Preserve canonical ownership, security boundaries, and explicit unknown/blocked states.
- Run focused tests and report changed files, checks, failures, and remaining runtime evidence.
- Do not claim Cloudflare or production success from source inspection or CI alone.

### Researcher

- Consult relevant project documentation and external technical references.
- Record source identity, retrieval date, scope, and uncertainty.
- Distinguish documentation facts, external claims, benchmark observations, and live runtime evidence.
- Do not turn a documentation lookup into a production acceptance receipt.

## Advisor triggers

Ask for an advisor review:

1. Before committing to a large or cross-repository plan.
2. When the same error or boundary failure occurs for the second time.
3. Before declaring a long-running task complete.

The review must state: scope, affected authorities, evidence already available, missing evidence, risks, and a proceed/revise/blocked decision. The advisor does not replace the main session's final verification.

## Evidence ladder

`implemented -> tested -> CI_green -> integration_verified -> runtime_verified -> production_certified`

Evidence cannot be promoted by wording. A merged PR is not a deployment; a successful workflow is not automatically runtime certification.

## Family boundaries

- Foundation owns public-safe contracts, public CI, and canonical production deployment.
- Operations owns protected runtime, policy, resource, evaluation, recovery, and promotion behavior.
- Operations must not gain GitHub Actions workflows or a competing deployment authority.
- Cloudflare changes require exact worker identity, revision/version, configuration, and live receipt evidence.

## Local Claude Code settings

Repository files do not modify `~/.claude/settings.json`, `~/.claude/agents`, environment variables, or user-local advisor configuration. Local configuration must be inspected and changed separately by the developer. Existing agents that explicitly select a different model must be preserved and listed rather than silently overwritten.

## Completion packet

Every substantial task should leave:

- issue and PR references;
- exact repository revision(s);
- canonical owner and touched file surface;
- tests/checks and their result;
- completed evidence rung;
- remaining runtime, control-plane, provider, or administrative evidence;
- next reproducible action if blocked.
