# Agent Tree Implementation Plan — 2026-09-25

## Tracking

- Issue: #1155
- Draft PR: #1156
- Branch: `agent-tree-governance-2026-09-25`
- Scope: repository-side Claude Code-compatible governance and prompt templates

## Delivered in this branch

- [x] Add governed Explorer / Worker / Researcher contract.
- [x] Add three scoped prompts with `model: opus` and `effort: medium`.
- [x] Add advisor triggers for major plans, repeated failures, and long-task completion.
- [x] Reference governance from `CLAUDE.md`.
- [x] Preserve Foundation's canonical CI/CD and production deployment ownership.
- [x] Preserve the evidence ladder and exact-revision completion packet.

## Explicitly not performed

- [ ] No edits to the developer's local `~/.claude/settings.json`.
- [ ] No edits to local `~/.claude/agents` outside this repository.
- [ ] No environment-variable changes or advisor-disable override changes.
- [ ] No Cloudflare mutation or production deployment.
- [ ] No claim that the local Opus/effort settings are active until local Claude Code configuration is inspected.

## Acceptance sequence

1. Review the prompt templates and governance contract.
2. Run repository documentation/format checks applicable to the changed paths.
3. Confirm no Operations GitHub Actions or competing deployment authority was introduced.
4. Merge only after required checks and review are satisfied.
5. Separately inspect local Claude Code configuration and report existing model/effort/environment overrides without changing them automatically.

## Completion boundary

This plan improves development-agent orchestration. It does not certify GitHub Actions, Cloudflare bindings, nightly research, chatbot runtime behavior, or production deployment.

## AI-agent benchmark adoption

- [x] Reuse the existing provider-neutral agent-behavior scoring primitives instead of creating a second scoring engine.
- [x] Add a six-lane project-native AI-agent task matrix covering planning, implementation, verification, research/evidence, security/reliability, and cross-language portability.
- [x] Require three repeat observations where stochastic execution is available.
- [x] Require exact revision, agent role, model/provider, evidence tier, and artifact provenance in benchmark observations.
- [x] Separate numeric benchmark scores from hard security/policy/provenance/runtime gates.
- [x] Add a Foundation-only contract-validation workflow; Operations remains without GitHub Actions.
- [ ] Run the first baseline matrix across the selected models/agents and retain the result artifacts.
- [ ] Convert reproducible benchmark failures into regression fixtures or agent-policy improvements.

The benchmark adopts the same audit philosophy as the project's polyglot scan: independent lanes, language diversity, differential testing, adversarial cases, evidence tiers, exact revisions, and explicit non-closure states.
