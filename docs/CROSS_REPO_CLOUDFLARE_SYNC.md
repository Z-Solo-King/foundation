# Cross-repo + Cloudflare synchronization record

Snapshot: 2026-09-29 (Asia/Kolkata)

## Authority model
- GitHub `main` trees are repository source truth.
- Cloudflare live API state is deployed-runtime truth.
- Fresh GitHub workflow evidence is the release certificate.
- Dated audits/handoffs are historical evidence.
- Production and research Operations pins are intentionally independent.

## Current repository state
- Foundation main: `34fcae8638fc2fb591131d5e53a6cf47ebdbe0dd`
- Operations main: `068c3cff76f194dd0188f704fda191388e6694cb`
- Production Operations pin: `068c3cff76f194dd0188f704fda191388e6694cb`
- Research Operations pin: `9a942b0f8cc601f8d460ed71ccba908fa02e6c75`
- Operations contains no `.github/workflows`; Foundation owns automation.

## Current Cloudflare topology
- Pages project: `ai` -> `ai-cio.pages.dev`
- Public Worker: `heroic`, workers.dev disabled
- Private edge Worker: `operations-edge`
- Private core Worker: `operations`
- D1: `research-intelligence`
- Legacy `foundation` Worker: retired
- Retired Pages aliases: `heroic`, `heroic-ai`
- Dated probe Workers and their temporary Queue consumer: retired

## D1 verification — 2026-09-29
- `d1_migrations` exists and migrations 1–10 are applied.
- Direct `sqlite_master` inspection returned the operational tables and indexes.
- No DDL was changed by this audit.

## Security/runtime authority
- Production moderation policy is `block`.
- Strict zero-cost policy is enabled; paid/unknown-pricing fallback remains disabled.
- Production task-envelope verification uses a dedicated `TASK_SIGNING_ROOT`; its value is never stored in Git or documentation.
- Fresh production certification must verify the exact immutable Operations pin and post-deployment runtime behavior.

## Documentation hygiene
Do not copy secret values, Cloudflare account IDs, private Worker origins, mutable deployment IDs, or mutable issue counts into current public-state documents. Historical documents remain useful only as provenance.
