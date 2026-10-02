# Cross-System CrossFire Standard

## Purpose

The family audit compares Foundation and Operations as one system without collapsing
their ownership boundaries. The audit model treats `N² x N² = N⁴` as typed
Cartesian comparison: policies, feature domains, functions, files, and architecture
edges are compared independently.

## Evidence model

`exact` means the compared contract text is identical.

`scope-only` means a responsibility exists in one repository by design and is not
expected in the other.

`overlap` means two surfaces appear related and need authority review; it is not
proof that either implementation is wrong.

`divergent` is a shared contract with conflicting definitions and is a strict gate.

`runtime-unverified` remains the state whenever repository evidence cannot establish
a live Cloudflare/runtime fact.

## CrossFire lanes

1. ownership/policy
2. TypeScript edge/application
3. Rust deterministic kernels
4. Go concurrency/network
5. Cloudflare/runtime/deployment
6. security/evidence/provenance

Completed lanes work-steal the next independent task. Shared writes remain serialized
through the canonical owner.

## AI provider cross-fire

The provider benchmark permits up to six configured direct providers, with three
repeats and bounded concurrency. Fewer than two configured direct providers is a valid
`comparison_unavailable` receipt, not a false comparative result.

AI output is supporting evidence only. Provider ranking, benchmark scores, or language
scores cannot transfer policy or correctness authority.

## Closure

The audit closes only after:

- all supplied tracked files are inventoried;
- all policy catalogs are loaded;
- all feature domains are pairwise reviewed;
- all function surfaces are scanned for cross-family name overlap;
- exact duplicate file content is surfaced;
- shared policy divergence is absent;
- required focused differential/runtime evidence is green; and
- live runtime facts have fresh receipts where production claims are made.

## Execution discipline

CrossFire is intentionally fail-closed and evidence-separated:

1. parallel analytical lanes may read the same repository state independently;
2. lanes do not share intermediate conclusions before their individual checks finish;
3. deterministic validators reconcile the independent outputs;
4. only the canonical owner may perform a mutation;
5. required GitHub checks must pass on the reconciled PR head before merge;
6. live Cloudflare verification is performed after deployment, not inferred from source state.

The six-provider target is an execution target, not a requirement to fabricate providers that are unavailable. A strong comparison requires at least five independent provider lanes; otherwise the receipt records the limitation explicitly.
