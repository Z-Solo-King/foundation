# Family Maintainability Standard

**Status:** normative; current
**Scope:** Foundation + Operations

## Goal

All active code must remain understandable, maintainable, updateable, fixable and safely removable by both humans and AI agents.

## Single owner

Every behavior, policy, algorithm, registry, state model, process and authority has exactly one canonical owner. Consumers use a typed/versioned contract, adapter or service boundary rather than copying implementation.

## Module contract

A non-trivial module should make its purpose and contract discoverable from its source and nearby tests:

- responsibility and non-responsibilities;
- inputs and outputs;
- invariants and validation rules;
- failure/unknown/partial behavior;
- side effects and external dependencies;
- canonical authority used by the module;
- compatibility/deprecation status where applicable;
- tests that protect the behavior.

Do not add comments that merely restate code. Explain non-obvious reasoning, invariants and ownership.

## Logic explanation standard

For every non-trivial production module, the owning source or its immediately adjacent canonical documentation must answer these questions in compact form:

1. **Why does this module exist?**
2. **What owns the decision it implements?**
3. **What enters and leaves the module?**
4. **What invariants must always hold?**
5. **What happens on success, rejection, failure, timeout, unknown or partial evidence?**
6. **What state or side effects can it change?**
7. **Which modules are allowed to call it?**
8. **Which tests prove the contract?**
9. **What is deliberately not implemented here?**
10. **What is the removal/migration path?**

Use a stable vocabulary for states and boundaries. Do not make an AI infer critical ownership or failure semantics from control-flow alone.

## AI navigation contract

AI agents should resolve work in this order:

1. repository role and boundary;
2. canonical ownership registry/map;
3. capability/module entrypoint;
4. governing contract/policy;
5. implementation;
6. owner-level tests;
7. cross-repository contract tests;
8. live/runtime evidence when required.

Prefer one canonical source plus short indexed references over repeated explanations in multiple documents. Generated maps are navigation aids, not independent authorities.

## Change methodology

Before implementing a material change:

1. Search both repositories for existing behavior and related tests.
2. Identify the canonical owner and existing authority.
3. Reuse or extend the owner before creating a new module.
4. Keep the public/private boundary explicit.
5. Prefer the smallest stable contract that solves the consumer need.
6. Add owner-level tests and boundary/contract tests for cross-repository behavior.
7. Run the appropriate repository validation and family overlap checks.
8. Update the canonical documentation when ownership, contracts, policy or methodology changes.

## Splitting and moving code

Split a module when responsibilities, lifecycle, ownership or change frequency are materially independent. Do not split only to reduce line count.

Move code between repositories only when ownership requires the move. Before moving, identify imports, entrypoints, state, tests, contracts and compatibility requirements. After migration, remove the old implementation once parity evidence shows it is no longer required.

A migration is not complete while the old implementation remains an alternative authority unless it is explicitly marked as a compatibility or rollback surface.

## Duplicate-prevention rules

Never introduce a second implementation of:

- authorization/policy decisions;
- identity or trust validation;
- resource/quota accounting;
- routing/intent authority;
- result-state semantics;
- provider eligibility policy;
- evaluation/promotion decisions;
- deployment ownership;
- deterministic Foundation-owned product/evidence algorithms.

Compatibility facades may preserve an API, but business logic remains in the canonical owner.

## AI maintainability and token efficiency

AI agents should prefer precise navigation and canonical references over repeatedly loading large duplicated context. Use repository maps, ownership indexes, contracts and focused tests to locate the correct implementation.

Token efficiency must never be achieved by omitting required constraints, evidence, failure states or ownership information. Prefer compact canonical records, structured contracts and generated/test fixtures over copied explanatory prose or duplicate code.

AI-generated changes must be explainable from the owning source, tests and linked documentation without relying on the original chat transcript.

## Removal and deprecation

At substantial milestones inspect for dead code, unreachable paths, obsolete feature flags, stale compatibility shims, duplicate tests, generic coverage files, superseded documents and abandoned branches/PRs where controls permit cleanup.

Remove only after checking imports, runtime entrypoints, tests and documented dependencies. Preserve Git history and record the reason when deletion could otherwise be ambiguous.

## Documentation rule

Do not create a new plan, policy or guide merely because a new conversation occurred. Update the canonical owner document when possible. Deferred, experimental, rejected and future-use material must have an explicit lifecycle state and revisit condition.

Operational live-state records, credentials/identifiers, deployment details and private topology belong in Operations, not in the public Foundation documentation surface.

## Completion standard

A maintainability change is complete only when ownership is singular, consumers are understood, tests cover the relevant contract, documentation is current, obsolete paths are removed or explicitly retained as compatibility/history, and no unsupported duplicate authority remains.