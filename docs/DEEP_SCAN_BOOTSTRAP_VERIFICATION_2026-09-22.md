# Deep-Scan Bootstrap Verification — 2026-09-22

This is a controlled post-merge validation change for the corrected open-issue polyglot deep-scan workflow.

The workflow no longer performs an unrelated editable install of the entire private Operations package. Its contract validation invokes the repository-local scan-contract functions directly with Python 3.14; the scanner itself uses only Python standard-library modules.

The purpose of this change is to verify the corrected `main` workflow under `pull_request_target`, where the base workflow is authoritative for private Operations checkout and credentials.

Expected post-fix gate:
- four lanes: L1, L2, L3, L4;
- 14 issues per lane;
- 56 unique issue×lane cases;
- zero FAIL results;
- complete lane receipts;
- aggregate PASS.
