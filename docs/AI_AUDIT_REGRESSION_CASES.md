# AI Audit Regression Cases

Permanent warnings for future AI-assisted audits.

| Case | Wrong inference | Required correction |
|---|---|---|
| Compatibility facade | A short module was called a stub. | Read the file and trace imports/exports. |
| Partial retry claim | Failure classification was treated as the retry loop. | Separate eligibility/classification from execution retry. |
| Context claim | A recent-history slice was treated as the entire context policy. | Inspect budgets, compaction, and tests. |
| Streaming claim | Lack of token streaming was confused with lack of streaming transport. | Distinguish upstream token streaming, buffered generation, and SSE transport. |
| CI failure | Zero-step jobs were called test failures. | Classify as pre-runner until repository execution is proven. |
| Production claim | Workflow/source was used as production evidence. | Require L4 runtime evidence. |
| Stale revision | Findings from an old branch were mixed with current main. | Record and verify exact SHAs. |
| Mergeability | `mergeable=true` was treated as acceptance. | Verify required checks and rulesets. |
| Client authority | Client-supplied system history was trusted as model authority. | Reject external system messages; server policy owns system instructions. |

## Invariant

A finding is complete only when evidence supports the exact claim, counter-checks were performed, and the acceptance gate is satisfied.

| Peer-audit isolation | One audit family's PASS was used to dismiss another family's finding. | Compare shared finding categories across independent audits; preserve corroborated, single-observer and disagreement states. |
| Audit drift | A newer scan changed coverage/methods/closure semantics without updating the other audit families. | Compare method contracts and false-positive controls after every material scan and record the delta as a regression rule. |
| Revision disagreement | Findings from different repository SHAs were combined into one conclusion. | Reconcile exact Foundation/Operations revisions before comparing observations. |
