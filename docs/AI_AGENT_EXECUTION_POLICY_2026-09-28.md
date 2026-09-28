# AI Agent Execution Policy — 2026-09-28 (Foundation public-safe)

> Public-safe continuation addendum. Foundation AGENTS.md remains the baseline. This document governs cross-chat continuity, issue burn-down and public-boundary execution details.

## 1. Connector separation

This project uses separate GitHub and Cloudflare chats.

### GitHub chat
- Work on Foundation/Operations repository code, issues, PRs, tests, GitHub Actions and documentation.
- Do not invoke or claim Cloudflare production mutations or runtime verification from this chat.
- Treat Cloudflare state as an external/runtime evidence gate until a protected runtime receipt exists.

### Cloudflare chat
- Live Worker, D1, secret, binding, deployment and production verification belongs to the Cloudflare chat.
- Runtime results must be reflected back into the repository evidence trail before they are treated as project state.

Shared state is carried by repository handoffs/current-state documents, not conversational assumptions.

## 2. Fast queue method

Use:
live GitHub inventory -> canonical-authority clustering -> cross-fire validation -> current-main branch -> smallest safe slice -> focused tests -> PR -> green checks -> merge -> issue evidence -> rescan

Keep 3–4 read-only lanes active. Serialize all mutations.

## 3. Cross-fire

Cross-fire is independent validation, not duplicate implementation.
- Lens 1: source and canonical-authority review.
- Lens 2: focused tests/CI, evidence fixture, or current technical documentation.

Runtime/L4 acceptance still requires real runtime evidence.

## 4. Mutation integrity

Before every write:
- verify current main/base;
- verify exact blob SHA;
- verify source contents are real and not a retrieval placeholder;
- check active PR/file ownership;
- avoid stale/conflicted branches.

After every write:
- re-read the file;
- inspect the diff/PR;
- run the narrowest relevant validation.

If a branch becomes stale/conflicted, use a fresh current-main branch and replay only verified intended changes.

## 5. Public/private boundary

Foundation may expose only public-safe contracts, diagnostics, evidence and response fields.
Private credentials, private prompts/results, memory, provider secrets, protected policy and Operations topology remain outside Foundation.

Do not weaken public security to make private integration easier.

## 6. Evidence ladder

R0 contract -> R1 tests/CI -> R2 integration -> R3 protected runtime -> R4 production.

Source inspection and repository tests cannot satisfy R3/R4.

## 7. Current Foundation checkpoint

- main code checkpoint: 75a79a37775cc9f410916c47ac2b5ac8c50bf775
- open issues: #1249, #1247, #157, #58
- open PRs at checkpoint: #1439, #1427

The earlier 24-open / approximately 14-new count was a transient snapshot and is not current queue authority.

## 8. Session-limit handoff

When a chat approaches its limit, update docs/CHAT_CONTINUATION_HANDOFF_2026-09-28.md and docs/CURRENT_SOURCE_OF_TRUTH.md with the latest verified repository state and next action.

Never make the next chat reconstruct material state from message history alone.

The next chat is a continuation, not a restart.