# Evidence Validation Contract

**Status:** Canonical family validation contract
**Owner:** Foundation family governance; Operations is the protected-runtime consumer.

## Evidence tiers

- **L1 — repository/source:** direct inspection of current repository state.
- **L2 — deterministic execution:** local/approved deterministic tests against the inspected revision.
- **L3 — automation execution:** GitHub Actions or other authorized automation with retained run identity and outputs.
- **L4 — approved private/external runtime:** execution of the real private service/runtime boundary with retained inputs, revision identity and outputs.
- **Production certification:** explicit production evidence from the production owner; L4 is not automatically production certification.

## Claim discipline

A validation result records, where applicable: revision, environment, execution/run identity, scope, checks actually executed, result state, timestamp/freshness and relevant artifacts/receipts.

`NOT_ATTEMPTED`, `UNKNOWN`, `BLOCKED`, `PARTIAL`, `FAILED` and `COMPLETE` are distinct states. A check that did not execute cannot be counted as healthy. A successful deterministic test cannot prove an unexercised external dependency. Source inspection cannot prove runtime or production behavior.

## Authorized environments

The required evidence tier is independent of the operator that obtains it. Authorized humans, automation and approved private/self-hosted runtimes may produce evidence when permitted. Tool or connector unavailability does not change the required tier and must not become an application dependency.

## Completion rule

An issue is complete only when its repository implementation criteria are satisfied and, where the issue explicitly requires runtime/production evidence, that evidence is retained at the stated tier. Implementation completion and runtime certification are separate dispositions.
