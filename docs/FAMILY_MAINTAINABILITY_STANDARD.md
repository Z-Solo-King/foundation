# Family Maintainability Standard

**Status:** normative; current  
**Scope:** Foundation + Operations

## Goal

Active code and documentation must remain understandable, maintainable, safely changeable and safely removable by humans and AI agents.

## Single owner

Every behavior, policy, algorithm, registry, state model and process has one canonical owner. Consumers use typed/versioned contracts, adapters or service boundaries rather than copying implementation.

## Change sequence

`search both repositories -> identify owner -> inspect consumers/side effects -> extend owner -> minimal stable contract -> focused owner/boundary tests -> validation -> update canonical docs -> remove obsolete duplicate`

## Module placement and splitting

Split by responsibility, not arbitrary size:

1. what changes together;
2. caller/hot-path/setup boundary;
3. trust/authority boundary;
4. I/O versus pure computation.

Soft design ceilings are trip-wires, not targets:

- function/method ~40 lines;
- module ~400 lines;
- class ~200 lines or 10 public methods;
- function signature ~5 parameters.

Crossing a ceiling is a prompt to inspect cohesion, not proof of a defect. Characterize behavior before structural extraction and keep extraction separate from bug fixes.

## Plain-language and engineering honesty

A config field that can only ever legally have one value is dead flexibility or an invariant, not genuine configurability.

A claim such as canonical, authoritative or complete must be checkable against current repository state or explicitly marked as intended/unverified.

Comments should explain why an invariant exists, not restate code.

## Duplication prevention

Never introduce a second authority for:

- authorization/policy;
- identity/trust;
- resource/quota accounting;
- routing/intent;
- result-state semantics;
- provider eligibility;
- evaluation/promotion;
- deployment ownership;
- deterministic Foundation algorithms.

Compatibility facades may translate names/shapes but must not repeat business logic.

## Documentation lifecycle

Do not create a new plan because a new conversation happened.

Living documents should carry current architecture, ownership, contracts and methods. Dated records are historical unless they preserve unique evidence/decisions. Proposed, experimental, deferred, rejected, superseded and obsolete material must have explicit lifecycle state.

At milestones inspect for duplicate documents, stale plans, dead code/tests, obsolete compatibility paths and abandoned branches/issues where supported.

## Removal discipline

Before deleting code or docs, check references/imports/entrypoints/tests and preserve Git history. Delete only after the unique current value has been transferred to the canonical owner.

## AI efficiency

Use maps, contracts, focused tests and canonical references rather than repeatedly loading duplicated context. Token efficiency must never omit required constraints or evidence.
