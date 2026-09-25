# LIVE PROJECT STATE

Audited: 2026-09-25
Authority: live GitHub repository state, GitHub Actions receipts/artifacts, and Cloudflare control-plane/runtime reads.
Purpose: canonical cross-chat continuation point for GitHub + Cloudflare + ChatGPT project work.

## 1. GitHub state

Authenticated GitHub account: Z-Solo-King

Foundation
- Repository: Z-Solo-King/foundation
- Visibility: public
- Default branch: main
- Audited main head: 07e12f5a1566ad216fbb998e31bd3a5e144e6d81
- Open issues: #58, #157, #1157
- Open PRs: #1203
- PR #1203 is documentation-only, clean/mergeable, and its current head has 12/12 checks passing.
- No open implementation PR.

Operations
- Repository: Z-Solo-King/operations
- Visibility: private
- Default branch: main
- Audited main head: 3c5b6a45ca2017548f4b8b97d43a25af6f562084
- Open issues: #145, #197, #340, #385, #597, #603, #699, #713
- Open PRs on Operations main snapshot: #914, #915
- Operations canonical live-state documentation merged as commit 3c5b6a45ca2017548f4b8b97d43a25af6f562084
- PR #914: pytest-asyncio dependency range update; current PR checks are not exposed by the connected GitHub endpoint.
- PR #915: setuptools dependency range update; current PR checks are not exposed by the connected GitHub endpoint.
- Both Dependabot PRs target an older Operations base than the current main and should be treated as dependency-maintenance branches, not current main evidence.

Repository open-issue API totals include pull requests:
- Foundation open_issues_count = 4 = 3 issues + 1 PR.
- Operations open_issues_count = 10 = 8 issues + 2 PRs.

Closed items that must not be reintroduced from stale prose:
- Foundation #154 is closed/completed.
- Operations #693, #711, and #352 are closed/completed.
- Operations #713 had been closed but is reopened from fresh 2026-09-25 CI evidence because URL-policy parity is still failing.

## 2. Open issue classification

Foundation
- #58 — umbrella coverage/evidence tracker; not an implementation defect by itself.
- #157 — canonical 24-program nightly research acceptance; currently blocked at production/public-domain readiness.
- #1157 — project-native AI/agent benchmark and cross-language evaluation matrix; planning/evidence work.

Operations
- #699 — umbrella deep-scan/security/reliability/migration tracker.
- #603 — AI-model/tooling portability evidence gate.
- #597 — mapper migration/decomposition and parity evidence.
- #385 — cross-surface terminalization/recovery evidence.
- #340 — governed provider streaming/token-accounting live evidence.
- #197 — conversational live acceptance evidence.
- #145 — periodic maintenance live receipt.
- #713 — Rust URL identity security/parity defect; reopened after current CI reproduced Python/Rust disagreement on corpus case u47.

Evidence rule: an open issue may represent missing L3/L4 evidence rather than unmerged repository code. Do not close from unit tests, source inspection, or deterministic CI alone when its contract requires runtime evidence.

## 3. Current Foundation CI / runtime gates

Passing on current Foundation main:
- Family integrity gate.
- Canonical workflow bridge acceptance.
- Main-push Actions control-plane probes.
- Nightly research contract.
- Open-issue polyglot deep scan.
- Polyglot migration review.
- Coverage-driven runtime matrix.
- Six-lane audit and dynamic issue×lane checks on PR #1203.
- Live extractor benchmark run 447.

Currently red on current Foundation main:
- Heroic AI production release run 586 / 36119831998.
- Nightly research provider preflight run 157 / 36119831965.
- Public Worker live probe run 157 / 36119831989.
- Hybrid language pilots run 187 / 36119832079.

Nightly multi-agent research run 374 / 36119847621 is still in progress and is waiting for the exact production-release gate. No live 24-program provider-backed acceptance has been certified.

### Current CI failures requiring tracking

1. Production/public DNS boundary
- Production release failed after repository tests and GitHub App/private-Operations authorization succeeded.
- Cloudflare prerequisite reports heroic-ai.dev is not an active zone.
- Provider preflight: HTTP 000, curl exit 6, dns_or_network_unreachable.
- Public Worker probe fails at the same DNS boundary.
- Provider configuration is present; this is no longer a missing research-secret diagnosis.

2. Rust URL identity parity
- Hybrid run job 108022531773 failed on case u47.
- Python reference accepted http://64:ff9b::127.0.0.1/
- Rust candidate returned target host is not allowed.
- Operations #713 is reopened for the existing URL-policy parity/security scope.

3. TypeScript endpoint differential lane
- Hybrid run job 108022532439 failed before parity execution while checking out a resolved Operations ref.
- The checkout command contained an embedded newline/wildcard in the refspec and failed with Git invalid refspec / exit 128.
- This is workflow/ref-resolution evidence, not proof that the TypeScript endpoint implementation itself is functionally wrong.
- Track under the existing Foundation coverage/CI evidence surface rather than opening a duplicate defect unless the workflow owner confirms no existing issue covers it.

## 4. Latest extractor benchmark

Run: 36119832050
Run number: 447
Head: 07e12f5a1566ad216fbb998e31bd3a5e144e6d81
Artifact: 10857765019
Artifact: live-extractor-benchmark-40way
Artifact SHA-256: c110306bffb021b51ffd304562f25bd77d010aadd81fa538871cfad7ab772544

Aggregate receipt:
- pass = true for the strict structural quality contract
- 40 receipts total
- platform coverage: API 12, browser 8, feed 8, HTML 12
- 4 ok, 32 empty, 4 blocked
- completion_rate = 0.1
- error_rate = 0.0
- invalid_resource_rows = 0
- missing_key_rows = 0
- provenance_completeness = 1.0
- route_provenance_completeness = 1.0
- repeat_reliability = 1.0
- unstable_repeated_groups = 0
- recovery_rate = 1.0

Interpretation:
This is a structural/integrity pass, not evidence that 40 real product acquisitions succeeded. Most cases were empty or blocked. The four ok receipts include a synthetic ecommerce case whose extracted record was only a listing-level placeholder with no price/brand/specs/images. Four Fake Store API repeats were blocked by HTTP 403. Keep benchmark status precise: contract-quality pass, business-data completeness unresolved.

## 5. Cloudflare live state

Account: connected and readable.

Canonical Workers present:
- foundation
- operations

Legacy Workers still present:
- research-intelligence-engine-public
- research-intelligence-engine-private

Current canonical Worker settings:
- foundation: production, assets/modules enabled, D1 DB bound, OPERATIONS service binding, strict-zero-cost-only enabled.
- operations: production, scheduled + fetch handlers, D1 OPERATIONS_DB bound, Cloudflare Workers AI configured, strict-zero-cost-only enabled.

Canonical Worker deployment provenance currently reported by Cloudflare:
- foundation: github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c
- operations: github:a3171f353539f1a31020c432f98cf0530cbf91ef

Therefore:
- GitHub main heads are not identical to the current Cloudflare canonical Worker deployment provenance.
- The immutable certified production pins documented by prior acceptance remain separate from current main and must not be inferred from branch position.
- A current main push is not production certification.

Domain/zone:
- zone: heroic-ai.dev
- zone status: pending
- activation failure reason: unresolvable
- Worker Domain: heroic-ai.dev -> foundation, production, enabled
- canonical public URL: https://Heroic-Ai.dev
- Current GitHub preflight cannot resolve the public hostname.

This domain activation/DNS state is the current production blocker.

D1:
- database: research-intelligence
- id: 19f51638-47a5-4218-a9dc-73dbfd6156fe
- read/query access: HTTP 200
- schema query executed read-only with 0 writes
- research_runs: 442 completed, 202 planned
- research_publications: 0 rows
- no maintenance_receipts table; maintenance acceptance must use the documented scheduler/runtime receipt path instead of inventing a D1 table.

## 6. Nightly research

Canonical workflow: Foundation nightly multi-agent research.
Current run: 36119847621 / run 374
State at audit: in_progress, waiting for exact production release.

Current preflight:
- research endpoint configured: yes
- research API key configured: yes
- research model configured: yes
- Worker health resolution: fails before HTTP because Heroic-Ai.dev does not resolve
- worker_ai_path_verified: false

No provider-backed 24-program receipt is currently certified.

## 7. ChatGPT continuity rules

- ChatGPT/UI state is transport state only.
- GitHub commits, workflow runs, artifacts, and Cloudflare runtime/control-plane receipts are authoritative.
- Always refresh current main heads and open queues before mutation.
- Separate current branch heads, immutable production pins, actual Cloudflare deployment provenance, and historical checkpoints.
- Keep heavy multi-step work resumable; use this file as the cross-chat continuation point.
- Do not claim runtime closure from repository CI when the issue requires L3/L4 evidence.
- Preserve historical sections for provenance, but use this file for current-state interpretation.

## 8. Canonical next gates

1. Restore Cloudflare zone activation/DNS for heroic-ai.dev and re-run production release.
2. Re-run public Worker probe and nightly provider preflight after DNS is active.
3. Allow nightly run 374 to complete only after its exact production gate passes; require complete 24-program provider-backed artifacts.
4. Resolve or formally disposition the TypeScript endpoint refspec workflow failure.
5. Fix Rust URL identity parity under Operations #713 and pass the shared negative/adversarial corpus.
6. Continue the remaining open evidence gates; do not close them from stale issue-body prose.

## 9. Snapshot semantics

This file records the live audited state at the time of the 2026-09-25 verification. Documentation commits may advance main after this snapshot; the snapshot remains a timestamped evidence record, not a self-referential claim about a future commit.
