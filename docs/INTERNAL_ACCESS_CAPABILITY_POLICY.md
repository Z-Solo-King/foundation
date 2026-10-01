# Internal Access Capability Policy — 2026-10-01

## Core rule

Internal access is capability-scoped. Autonomous AI can request approved operations, but must not receive raw Cloudflare, Backblaze, GitHub-App, or provider secrets.

| Surface | Canonical access | AI access |
|---|---|---|
| Foundation | GitHub Actions checkout at exact ref | Requestable through allowlisted workflows |
| GitHub Actions | job-scoped `GITHUB_TOKEN` | Dispatch approved workflows; inspect runs |
| Private Operations source | short-lived GitHub App token, repo-scoped | Read approved source/revisions |
| Chatbot | Foundation authenticated API -> private service binding -> Operations | Request governed model generation |
| Cloudflare | dedicated deployment/reconciliation workflow + Worker service bindings | Request approved workflow only |
| Backblaze B2 | protected runtime/backup workflow | Request backup/restore workflow only |
| Operations D1 | `OPERATIONS_DB` binding | Indirectly via governed handlers |
| Provider fleet | Operations `AI` binding + provider policy | Request model/planning work |
| Production release | existing release gate | Not autonomously dispatchable |

## Live Cloudflare topology checked 2026-10-01

`heroic -> heroic-core -> operations-edge -> operations`.

`heroic` binds `CORE=heroic-core`.
`heroic-core` binds D1 `DB`, service `OPERATIONS=operations-edge`, and B2 `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET`, `B2_ENDPOINT`.
`operations-edge` binds `CORE=operations`.
`operations` binds AI `AI`, service `FOUNDATION=heroic`, D1 `OPERATIONS_DB`, and protected chatbot/provider configuration.

Live Cloudflare annotations:
- public Foundation revision: `f43028ca6c6a4f4d3cecbfdb99ae4602330228b4`;
- deployed Operations revision: `90fa37df10d63824acd3fe20b64cc91043af9627`.

No secret values belong in this document.

## Access rules

1. Prefer service bindings for internal Worker-to-Worker calls.
2. Prefer short-lived GitHub App installation tokens for private Operations source access.
3. Grant GitHub permissions per job, not globally.
4. Never expose Cloudflare/B2/provider credentials to model prompts, issue bodies, artifacts, or planner context.
5. B2 is storage/backup authority only.
6. Operations is private runtime/policy authority; Foundation is GitHub Actions authority.
7. AI can select a workflow only from the deterministic allowlist and may not invent inputs or commands.
8. Missing credentials are a blocked state; never weaken policy to continue.

## GitHub Free private Operations control

GitHub's current documentation says branch protection/rulesets cover private repositories on Pro/Team/Enterprise, while GitHub Free supports them for public repositories. Native protected-main enforcement therefore cannot be relied upon for this private Operations repository.

The project uses a compensating control:
`Operations main -> Foundation integrity guard -> immutable approved SHA -> production/runtime`.

The guard runs every 15 minutes, reads Operations through the read-only GitHub App, verifies privacy/default-branch/no-workflow invariants, compares `main` to the Foundation approval manifest, and creates a durable incident on drift. It never force-resets Operations.

This does not stop the underlying push; it prevents an unapproved private `main` commit from silently becoming production authority.
