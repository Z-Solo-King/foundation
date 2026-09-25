# Agent Tree Implementation Plan — 2026-09-25

## Tracking

- Issue: #1155
- Draft PR: #1156
- Branch: `agent-tree-governance-2026-09-25`
- Scope: repository-side agent-tree governance, Claude-compatible prompt templates, and the public AI-agent benchmark contract

## Delivered in this branch

- [x] Add governed Explorer / Worker / Researcher contract.
- [x] Add three scoped prompts with `model: opus` and `effort: medium`.
- [x] Add advisor triggers for major plans, repeated failures, and long-task completion.
- [x] Reference governance from `CLAUDE.md`.
- [x] Preserve Foundation as the sole CI/CD and production deployment authority.
- [x] Preserve the evidence ladder and exact-revision completion packet.

## AI-agent benchmark adoption

- [x] Reuse the existing provider-neutral agent-behavior scoring primitives instead of creating a second scoring engine.
- [x] Add a 24-task project-native benchmark matrix across six audit-inspired lanes: planning/architecture, code/implementation, testing/verification, research/evidence, security/reliability, and cross-language portability.
- [x] Tie benchmark tasks to real Heroic AI issues/surfaces including #157, #282, #340, #385, #597, #603, #699 and #145.
- [x] Use Python, TypeScript/Worker, Rust/systems, YAML/JSON/Markdown, Go/concurrency, and Polyglot as analytical lenses.
- [x] Require three repeat observations where stochastic execution is available.
- [x] Require exact repository revision, agent role, model/provider, language lens, evidence tier, and artifact provenance.
- [x] Keep hard security/policy/provenance/runtime gates separate from numeric benchmark scores.
- [x] Add deterministic manifest validation and a Foundation-only contract workflow.
- [ ] Run the first multi-model/agent baseline and retain the per-run artifacts.
- [ ] Convert reproducible benchmark failures into regression fixtures or agent-policy improvements.

## Explicitly not performed

- [ ] No edits to the developer's local `~/.claude/settings.json`.
- [ ] No edits to local `~/.claude/agents` outside this repository.
- [ ] No environment-variable changes or advisor-disable override changes.
- [ ] No Cloudflare mutation or production deployment.
- [ ] No private Operations benchmark data copied into Foundation public artifacts.

## Acceptance sequence

1. Review the prompt templates, governance contract, and AI benchmark matrix.
2. Validate the benchmark manifest through the Foundation workflow.
3. Keep protected Operations benchmark scenarios private.
4. Run the same task/tool policy across candidate models and agent roles.
5. Retain per-run observations before aggregation.
6. Independently reproduce candidate findings before turning them into code or policy changes.
7. Merge only after required checks and review are satisfied.

## Evidence rule

Benchmark results are engineering observations. They do not replace security, policy, provenance, resource, migration, Cloudflare, runtime, or production acceptance gates and do not transfer authority to any model.

## Completion boundary

This plan improves development-agent orchestration and introduces a reproducible AI-agent evaluation layer. It does not certify GitHub Actions, Cloudflare bindings, nightly research, chatbot runtime behavior, or production deployment.
