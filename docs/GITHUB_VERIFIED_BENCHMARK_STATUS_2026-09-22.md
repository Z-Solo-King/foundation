# GitHub-Verified Benchmark Status — 2026-09-22

## Authoritative current repository state

- Foundation `main`: `0c3a7ad0f31f4dd42e18c2c9c77e248479daba4f`
- Operations `main`: `6479c11545a237f4bae3b0764c67e6bac2969241`
- Canonical immutable Operations production/nightly pin: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`
- Foundation production/deployment policy continues to require the immutable Operations pin; mutable `operations/main` must not be substituted into production authority.
- GitHub Actions remains the sole Foundation CI/CD and production deployment authority.
- Operations remains intentionally free of GitHub-hosted workflows.

## Deterministic verification completed in this GitHub-only pass

| Surface | Result | Notes |
|---|---|---|
| Foundation benchmark package / contract suite | PASS | Repository benchmark artifacts and contract modules validated against current `main`. |
| Foundation chatbot query benchmark | PASS | 29/29 deterministic corpus cases passed. |
| Foundation research-artifact validation | PASS | Catalog, corpus, schema and validator artifacts reconciled successfully. |
| Foundation open-issue four-lane reproduction | PASS | 56/56 issue×lane cases; L1–L4 had zero FAIL cases locally. REVIEW classifications are intentional. |
| Operations mapper/extractor cross-audit | PASS | 12/12 audited boundary checks passed. |
| Operations exhaustive audit contract | PASS | 5/5 current contract checks passed in the repository harness. |
| Resource-envelope semantics | PASS at current source level | Canonical settlement contract requires CONSUMED/RELEASED to account for the full reservation; the current test suite matches this contract. |
| Foundation PR #994 | MERGED | Added fail-closed `EvaluationCorpusManifest.__post_init__`; all 7 required GitHub checks reported success before merge. Merge SHA: `0c3a7ad0f31f4dd42e18c2c9c77e248479daba4f`. |
| CodeQL for PR #994 | PASS | GitHub check completed successfully. |

## Evidence boundary

The following are intentionally **not** claimed complete from repository-only evidence:

- Foundation #157: real provider-backed 24-program nightly execution.
- Foundation #452: real public-worker client disconnect/cancellation receipt.
- Operations #119/#132: real cross-version memory/replay receipt.
- Operations #145: approved live maintenance receipt.
- Operations #197: approved production duplicate/idempotency/policy-denial/restart receipts.
- Operations #340: live provider interruption/cancellation and resource reconciliation receipt.
- Operations #352: representative live 40-case extractor/mapper benchmark and replay/provenance receipt.
- Operations #385: cross-surface crash/recovery/late-output receipt.
- Operations #597/#603: measured migration parity/performance/shadow/canary/rollback evidence.
- Operations #711: real/preview D1 `changes()` semantics and concurrent over-limit evidence.
- Operations #699/#58: parent/meta closure until the required child evidence is discharged.

No runtime evidence has been fabricated or inferred from deterministic tests.

## Operational conclusion

Repository implementation and deterministic validation are current for this pass. The remaining open issues are genuine runtime/provider/Cloudflare/external-evidence gates rather than known unmerged implementation defects. Historical source-of-truth documents may retain older dated heads; this file is the current GitHub-only verification record for 2026-09-22.
