# AI Audit Regression Cases

These cases are permanent warnings for future AI-assisted audits. They are based on mistakes observed during repository review.

| Case | Wrong inference | Required correction |
|---|---|---|
| Compatibility facade | A very short module was called a stub. | Read the complete file and trace its imports/exports. Compatibility exports are delegation, not missing implementation. |
| Partial retry claim | Existing failure classification/eligibility was treated as if no retry mechanism existed. | Separate classification/eligibility from the execution retry loop and name the exact missing layer. |
| Context claim | A simple recent-history slice was treated as the entire context policy. | Inspect token budgets, compaction, and tests before declaring context management absent. |
| Streaming claim | Lack of upstream token streaming was confused with absence of streaming transport. | Distinguish provider-token streaming, buffered generation, and transport-level SSE. |
| CI failure | Jobs with zero steps and no runner/log metadata were described as code/test failures. | Classify as pre-runner infrastructure failure until repository execution is proven. |
| Production claim | Repository/workflow source was used to claim live deployment or runtime state. | Require approved L4 runtime evidence. |
| Stale revision | Findings from an old branch/base were combined with current main. | Record exact head/base SHAs and re-check current revisions. |
| Mergeability | `mergeable=true` was treated as acceptance. | Required checks and rulesets must actually pass. |
| Client authority | Client-supplied system history was treated as trusted model instruction. | Reject/discard external `system` messages; server-owned system instructions are authoritative. |

## Audit invariant

A finding is not complete because it sounds plausible. It is complete when the evidence supports the exact claim, the counter-check was performed, and the acceptance gate is satisfied.
