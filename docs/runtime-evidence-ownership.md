# Runtime-evidence ownership

Documentation only. No code or workflow changes.

**Current boundary — 2026-09-24:** GitHub repository and Actions state can be checked from the GitHub connection used for this chat. Cloudflare Worker/runtime state requires the dedicated Cloudflare connection and must not be inferred from GitHub-only evidence.

Repository-side implementation for the open acceptance issues is merged (see META #58). What remains is
evidence that can only be produced in a live environment. This page records who can produce each receipt,
so a limited-permission AI assistant does not guess at fixes it cannot verify.

## Ownership matrix

| Evidence needed | Issue(s) | Limited-permission AI | Owner with runtime access |
|---|---|---|---|
| Configure `RESEARCH_LLM_ENDPOINT`, `RESEARCH_LLM_API_KEY`, `RESEARCH_LLM_MODEL` Actions secrets | Foundation #157 | Cannot | Owner (repo admin) |
| Trigger and read the canonical 24-program nightly run and artifacts | Foundation #157 | Cannot | Owner |
| `persistence_seed`, redeploy, `persistence_verify`; paste JSON | Operations #119, #132 | Read-only D1 before/after checks | Owner (deploy + auth token) |
| Real maintenance receipt row | Operations #145 | Schema check only | Owner |
| D1 `changes()` inside a batch, concurrent over-limit probe | Operations #711 | Drift query only | Owner (preview D1) |
| Client disconnect/abort receipt through the public Worker | Foundation #452 | Cannot | Owner |
| Live provider interruption, idempotency collapse, policy denial | Operations #340, #197 | Cannot | Owner |
| Live extractor benchmark and replay | Operations #352, #597, #603 | Review reports once posted | Owner |
| Cross-surface recovery, crash after side effect | Operations #385 | Cannot | Owner |

## Rules of engagement for AI assistants

1. Do not propose new implementation for an issue whose body says the repository-side work is merged.
   Ask for the receipt instead.
2. Post read-only evidence (SELECT queries, schema checks) as issue comments, and label it as
   supporting evidence or a closing receipt.
3. Never manufacture or weaken evidence to close an issue.
4. If an action needs a permission the assistant lacks, say so in the issue and name the owner.
5. Never post secret values in issues, comments, or PRs.

## Historical note

An older reconciliation referenced a `maintenance_receipts` table and tracking issue #953. Operations #145 now explicitly defines the canonical acceptance path as the existing Worker `scheduled()` resource-governance reconciliation and its scheduler coordination; a nonexistent D1 table must not be used as acceptance evidence. A fresh live maintenance receipt is still required.
