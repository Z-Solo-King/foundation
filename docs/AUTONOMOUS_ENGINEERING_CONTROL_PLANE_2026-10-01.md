# Autonomous Engineering Control Plane — 2026-10-01

## Problem being solved

Interactive ChatGPT is not a suitable runtime dependency for long engineering jobs. The observed operating problems are session/usage limits, context/cache growth, mobile/app instability, connector throughput, and repeated manual chat handoffs.

The project therefore treats ChatGPT as an optional supervisor only. Engineering missions must continue when the ChatGPT app is closed, the current conversation reaches its allowance, the conversation becomes unresponsive, developer-mode/memory availability changes, or the GitHub connector in the chat is unavailable or slow.

The approximately 25-minute session duration is an observed project behavior, not a universal OpenAI product limit. Current OpenAI documentation describes plan/model-dependent usage limits rather than a fixed 25-minute runtime guarantee.

## Verified design basis

The project already has Foundation-owned GitHub Actions, Operations-owned AI provider/task fabric, multi-lens planning, persistent Cloudflare/D1 state, migration and feed workflows, and strict evidence/policy boundaries.

Operations exposes the governed AI task families `action_plan` and `workflow_assist`. Provider selection, retry, privacy, cost and resource policy remain centralized. The current provider contract covers eight external API families plus native Cloudflare Workers AI; Foundation currently activates seven external lanes and remains strict zero-cost.

## New autonomy principle

The critical loop is now:

event/schedule -> governed AI plan -> deterministic plan validation -> allowlisted GitHub workflow -> evidence -> verification -> persistent mission state -> next scheduled wake-up

It is no longer:

ChatGPT conversation -> connector calls -> growing context -> session limit -> manual handoff

A phone or computer does not need to remain online for the autonomous engineering loop.

## ChatGPT-specific requirements

1. No autonomous mission may depend on an open ChatGPT conversation.
2. No mission may require ChatGPT memory to restore state.
3. ChatGPT context is treated as disposable cache, never as canonical project memory.
4. Every substantial mission has a durable GitHub/Cloudflare state record and machine-readable receipt.
5. A new ChatGPT conversation must be able to inspect the same mission state without a special handoff.
6. Connector throttling or temporary connector failure must only pause the autonomous supervisor, not destroy mission state.
7. Interactive ChatGPT may inspect, override or approve a mission, but closing the app must not terminate it.
8. Long jobs are decomposed into bounded child workflows so no interactive model session must remain alive for the complete workload.

## Control-plane topology

```text
GitHub issue / schedule / workflow failure
                 |
                 v
       Autonomous supervisor
                 |
                 v
      Operations governed AI fabric
       action_plan / workflow_assist
                 |
                 v
       Machine-readable plan
                 |
                 v
      Deterministic mission router
                 |
                 v
        Foundation GitHub Actions
                 |
                 v
          Evidence + receipts
                 |
        +--------+--------+
        |                 |
      retry             blocked
        |                 |
        v                 v
     next wake-up     human/admin gate
```

Foundation remains the GitHub Actions owner. Operations remains the private AI/provider/policy owner. Cloudflare remains the deployed-runtime authority.

## Mission state

`queued -> planning -> planned -> executing -> verifying -> retrying | blocked | complete`

Every mission persists at least:

- mission_id
- mission_type
- Foundation SHA
- Operations revision/pin when relevant
- planning cycle
- workflow attempts
- child workflow run IDs
- plan digest
- provider/model identity when available
- terminal reason
- latest evidence/receipt reference

GitHub issue state is the v1 visible durable handoff. Detailed evidence remains in workflow artifacts and the existing D1/B2 evidence systems.

## Bounded autonomy

Autonomous v1 can:

- triage open work;
- request a governed plan;
- select an allowlisted workflow;
- dispatch the workflow at Foundation `main`;
- monitor the child run on a later wake-up;
- retry within explicit bounds;
- write bounded mission state/comments;
- stop truthfully when evidence is insufficient.

Autonomous v1 cannot:

- dispatch production release;
- alter secrets or credentials;
- change acceptance policy;
- bypass CAPTCHA, Cloudflare challenge, authentication or anti-bot controls;
- promote a new production authority;
- execute arbitrary shell supplied by the model;
- send arbitrary workflow inputs;
- retry indefinitely;
- treat model output as evidence authority.

## Allowed mission families

Migration:
`polyglot-migration-review.yml`, `open-issue-polyglot-deep-scan.yml`.

Feed recovery:
`woocommerce-clean-recovery.yml`, `native-google-feed-hunt.yml`, `woocommerce-identified-family-exhaustive-v5.yml`.

Nightly research:
`nightly-multi-agent-research-v3.yml`.

Audit:
`exhaustive-six-lane-audit.yml`, `cross-repository-contract-drift.yml`.

Runtime reconciliation:
`provider-fleet-runtime-state.yml`, `nightly-invariants.yml`, `operations-centralized-validation.yml`.

`heroic-ai-production-release.yml` is explicitly forbidden to the autonomous router.

## Failure semantics

There are five useful terminal/continuation classes:

1. `transient_provider` — wait for a later supervisor wake-up.
2. `transient_workflow` — retry only within the workflow-attempt limit.
3. `evidence_incomplete` — remain open; request another bounded evidence action.
4. `policy_blocked` — remain blocked; never weaken policy automatically.
5. `external_admin_required` — remain blocked until an authorized human/admin action occurs.

Maximum v1 planning cycles: 6 per mission. Maximum same-workflow dispatches: 3 per mission. No busy-loop polling after the supervisor invocation finishes.

## Why this solves the current ChatGPT failure mode

The project state is moved out of the conversation. The conversation can disappear without losing the plan, child run IDs, evidence or next action.

The ChatGPT app can therefore be used like a dashboard/reviewer rather than a server process.

## GitHub Agentic Workflows

GitHub Agentic Workflows are useful for repository reasoning, issue triage and safe outputs. Current GitHub documentation also makes clear that agentic workflows are not a substitute for durable multi-stage orchestration with job dependencies, external waits and rollback. The project therefore keeps deterministic Actions as the executor.

## Cloudflare evolution

Cloudflare Workflows/Agents are a strong v2 home for the durable mission state machine because they support persistent multi-step execution, retries, schedules and external-event waits. The v1 implementation stays GitHub-first so it does not create another deployment authority or require a new runtime deployment before the existing production preflight is healthy.

## Acceptance

A valid implementation must demonstrate:

1. mission creation without ChatGPT;
2. governed AI planning through the existing provider fabric;
3. deterministic plan rejection when the model proposes an unsafe/unknown workflow or non-empty inputs;
4. workflow dispatch from Foundation;
5. continuation from a later supervisor run after the first run exits;
6. bounded retry;
7. truthful blocked state;
8. machine-readable receipt;
9. no production-release authority transfer.

## Sources checked 2026-10-01

- OpenAI Help Center: ChatGPT plan/model usage limits
- OpenAI Help Center: Memory in ChatGPT
- OpenAI Help Center: ChatGPT Go
- OpenAI Help Center: Developer mode and MCP apps
- OpenAI Help Center: Codex with ChatGPT
- GitHub Agentic Workflows and safe-output documentation
- GitHub Actions workflow dispatch documentation
- Cloudflare Workflows documentation
- Cloudflare Agents / MCP / multi-provider AI documentation