# AI audit regression cases

Permanent warnings for future AI-assisted audits.

## Invariant

A finding is complete only when evidence supports the exact claim, counter-checks were performed, and the acceptance gate is satisfied.

| Peer-audit isolation | One audit family's PASS was used to dismiss another family's finding. | Compare shared finding categories across independent audits; preserve corroborated, single-observer and disagreement states. |
| Audit drift | A newer scan changed coverage/methods/closure semantics without updating the other audit families. | Compare method contracts and false-positive controls after every material scan and record the delta as a regression rule. |
| Revision disagreement | Findings from different repository SHAs were combined into one conclusion. | Reconcile exact Foundation/Operations revisions before comparing observations. |

## Live-head reconciliation

Before comparing audit outputs or treating a documentation statement as current, resolve the exact GitHub main heads and keep them separate from immutable runtime-certification pins. A documentation or migration commit must never be inferred to replace the approved production pin without its own promotion evidence.
