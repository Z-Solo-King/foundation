# Internal Access Capability Policy — 2026-10-01

## Purpose

This document defines the internal capability boundaries for the autonomous engineering system. “Access” means a specific approved operation path, not a bundle of reusable secrets.

The AI planner never receives the Cloudflare API token, Backblaze application key, GitHub App private key, or other deployment credentials.

## Capability matrix

| Surface | Canonical owner | Internal access path | AI may request | AI receives raw secret |
|---|---|---|---|---|
| Foundation source | Foundation | GitHub Actions checkout at an exact ref | Yes, through allowlisted workflow | No |
| GitHub Actions | Foundation | Job-scoped `GITHUB_TOKEN` with explicit permissions | Yes: dispatch approved workflows, inspect runs | No persistent token |
| Private Operations source | Foundation deployment/audit workflows | GitHub App installation token, repository-scoped and short-lived | Yes: read approved source/revision | No App private key |
| Chatbot | Operations | Foundation public API -> private service binding -> Operations auth boundary | Yes: request model generation through governed chatbot path | No provider keys |
| Cloudflare runtime | Cloudflare | Dedicated deployment/reconciliation workflow and Worker service bindings | Yes: request an approved deployment/verification workflow | No `CLOUDFLARE_API_TOKEN` |
| Backblaze B2 | `heroic-core` backup boundary | B2 credentials bound only to the protected runtime/backup workflow | Yes: request an approved backup/restore workflow | No B2 key |
| Operations D1 | Operations | `OPERATIONS_DB` binding | Indirectly through governed Operations handlers | No direct DB credential |
| Provider fleet | Operations | `AI` binding plus governed provider runtime | Yes: planner/model request | No provider API key |
| Production release | Foundation | Existing canonical release workflow | Request only; current autonomous router cannot dispatch it | No deployment secret |

## Live Cloudflare topology checked 2026-10-01

- `heroic` is the public edge and binds to `heroic-core` through service binding `CORE`.
- `heroic-core` contains the protected D1 binding `DB`, B2 bindings `B2_KEY_ID`, `B2_APPLICATION_KEY`, `B2_BUCKET`, `B2_ENDPOINT`, and service binding `OPERATIONS` to `operations-edge`.
- `operations-edge` binds `CORE` to the private `operations` Worker.
- `operations` contains the AI binding `AI`, private `AUTH_TOKEN` and `CHAT_BACKEND_TOKEN`, `OPERATIONS_DB`, and service binding `FOUNDATION` back to `heroic`.
- The production Operations Worker is currently annotated with Operations revision `90fa37df10d63824acd3fe20b64cc91043af9627`.
- The public `heroic` and `heroic-core` Workers are currently annotated with Foundation revision `f43028ca6c6a4f4d3cecbfdb99ae4602330228b4`.

No secret values are recorded here.

## Access rules

1. Prefer service bindings over external URLs for internal Worker-to-Worker calls.
2. Prefer short-lived GitHub App installation tokens over persistent personal access tokens for private Operations source access.
3. Use the minimum GitHub App repository permissions required by each workflow.
4. Use a job-scoped `GITHUB_TOKEN` for Foundation workflow operations.
5. Never pass Cloudflare or B2 credentials into a model prompt, issue body, artifact, or autonomous planner context.
6. Provider keys remain inside Operations; the planner sees only bounded provider identity/usage metadata.
7. B2 is storage/backup authority only. It is not an identity, routing, acceptance, or deployment authority.
8. Operations is the private policy/runtime owner. Foundation remains the GitHub Actions owner.
9. A model may select an approved workflow but may not invent a workflow, arbitrary workflow inputs, deployment commands, or secret names.
10. A credential missing at runtime is a blocked execution state, never a reason to disable a policy or bypass a boundary.

## Free-plan private Operations protection

GitHub documents that branch protection and rulesets are available on private repositories only with Pro, Team, or Enterprise; GitHub Free supports them for public repositories. Therefore this private repository cannot obtain native protected-branch enforcement on the current plan.

The project uses a compensating control:

`Operations main -> integrity guard -> approved immutable pin -> production/runtime consumers`

A change to Operations `main` does not automatically become production authority.

The guard:
- reads the private repository with the read-only Operations GitHub App;
- confirms the repository remains private and `main` remains the default branch;
- confirms the private repository still has no `.github/workflows`;
- compares `main` with the approved Operations SHA in Foundation;
- creates a visible integrity incident and fails the guard when `main` moves beyond the approved SHA;
- never rewrites or force-resets Operations `main` automatically.

The approved SHA is changed only through a reviewed Foundation pull request, so the control point itself remains on the public repository where GitHub Free protection is available.

This is not equivalent to a native pre-receive branch block: an unauthorized commit can still appear briefly on Operations `main`. The compensating control prevents that commit from silently becoming a production/runtime authority.

## Why this is the correct no-paid-plan strategy

The goal is not to imitate GitHub's UI. The goal is to enforce the security property that matters:

> unreviewed Operations code cannot become the code consumed by production.

Immutable production pins, a protected public promotion manifest, scheduled integrity detection, and runtime rejection of unapproved revisions provide that property without pretending the private repository has native protected-branch enforcement.
