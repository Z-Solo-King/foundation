# Cross-repo + Cloudflare synchronization record

Snapshot: 2026-09-29 (Asia/Kolkata)

## Current authority
- Foundation main: `0b2055fd05654bcbea20822fdc90f58859a8b856`
- Operations main: `068c3cff76f194dd0188f704fda191388e6694cb`
- Production Operations pin: `068c3cff76f194dd0188f704fda191388e6694cb`
- Canonical production workflow: `.github/workflows/heroic-ai-production-release.yml`
- Operations contains no GitHub Actions workflows.

## Current Cloudflare topology
- Pages: `ai` -> `ai-cio.pages.dev`
- Public Worker: `heroic` (workers.dev disabled)
- Private edge Worker: `operations-edge`
- Private core Worker: `operations`
- D1: `research-intelligence`
- Legacy `foundation` Worker: retired
- Legacy Pages aliases `heroic` and `heroic-ai`: retired
- Dated feed/browser/probe Workers: retired
- Probe Queue and consumer: retired

## Current D1 verification
- Direct `sqlite_master` query returned the expected operational tables and indexes.
- `d1_migrations` contains migrations 1 through 10, ending at `0010_public_admission.sql`.
- No DDL was changed during this audit.

## Current protected runtime state
- Operations production policy bindings: moderation `block`, strict zero-cost `true`, paid fallback `false`, unknown pricing `false`, max daily cost `0`.
- Dedicated Cloudflare Worker secret `TASK_SIGNING_ROOT` is provisioned for production task-envelope verification.

## Evidence rule
Repository state is authoritative for source/config. Cloudflare live API state is authoritative for deployed runtime. Fresh successful production workflow evidence is required before declaring the new revision certified.

## Documentation rule
Do not copy secret values, live credentials, Cloudflare account identifiers, private Worker origins or mutable deployment IDs into current-state documents. Keep unique historical evidence in `docs/history/`.
