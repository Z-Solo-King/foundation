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