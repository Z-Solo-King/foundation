# Current Source of Truth — Foundation (public-safe)

> **LIVE CHECKPOINT — 2026-09-27**
> This page is the public-safe current-state record. Historical handoffs remain historical and must not override the live GitHub state.

## HEADS
- Foundation main: `1be37629898a8d40ae4329ec70787b33d3934228`
- Operations: protected/private; current development head is tracked in the private Operations source-of-truth record.

## ISSUES
- Family open issue count: **11**
- Foundation: #58, #157, #1157, #1247, #1249
- Operations: 6 current security/maintenance/migration acceptance issues; private details remain on Operations.

## PRs
- Foundation open PRs: **#1344**, **#1354**
- Operations open PRs: **0**
- Foundation #1359 and Operations #1109/#1110 are merged and are not active implementation work.

## GROUPS
| Group | Canonical issues | Owner |
|---|---|---|
| AI research / benchmark / portability | #157, #1157, Operations portability track | Foundation + Operations |
| Feed recovery | #1247, #1249 | Foundation |
| Mapper migration | Operations mapper migration track | Operations |
| Security / control plane | Operations security tracks | Operations |
| Maintenance | Operations maintenance track | Operations |
| Master tracking | #58 | Foundation |

## CONNECTIVITY
- Cross-repository contract: `docs/FAMILY_CONTRACT.json`
- Integration topology: `docs/FAMILY_INTEGRATION_GRAPH.json`
- Sync state: `docs/FAMILY_SYNC_STATE.json`
- Prompt routing: `docs/PROMPT_TO_CANONICAL_DOC_MAP.md`
- Operations public/private boundary: `https://github.com/Z-Solo-King/operations`
- Foundation feed recovery PRs: `https://github.com/Z-Solo-King/foundation/pull/1344`, `https://github.com/Z-Solo-King/foundation/pull/1354`

## EVIDENCE
- Nightly 24-program research: no provider-backed closure receipt is certified.
- Extractor benchmark: 40 receipts; 4 `ok`, 32 `empty`, 4 `blocked`; structural/provenance checks passed, but this does not equal 40 successful real acquisitions.
- Polyglot migration: repository/deterministic evidence exists; runtime performance/resource/shadow/canary/rollback evidence remains the promotion boundary.

## OWNERSHIP
Foundation owns public-safe contracts/core, public edge/API, frontend, GitHub Actions and deployment orchestration.
Operations owns private provider control, quota/resource governance, private chatbot/runtime, recovery, protected tooling and migration runtime evidence.

## SYNC RULE
Use this page + `FAMILY_SYNC_STATE.json` as the compact public checkpoint. Fresh GitHub/runtime evidence outranks dated documents. Do not create a competing current-state document.