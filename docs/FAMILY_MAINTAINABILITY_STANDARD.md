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

## Completion standard

A maintainability change is complete only when ownership is singular, consumers are understood, tests cover the relevant contract, documentation is current, obsolete paths are removed or explicitly retained as compatibility/history, and no unsupported duplicate authority remains.
