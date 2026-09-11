# GitHub Family Member Contract

## Role

`foundation` is the public contract and reusable-primitives member of the three-repository family.

## Owns

- Public-safe domain contracts and schemas.
- Reusable deterministic application primitives.
- Canonical semantic interfaces consumed by private execution.

## Does not own

- Private acquisition credentials or secrets.
- Protected evaluation holdouts.
- Runtime cost authorization.
- Promotion, rollback, or deployment authority.
- Final trust decisions about extracted evidence.

## Family flow

`foundation contract -> extractor-mapper execution -> untrusted result -> operations gate`

Foundation may define what a valid object means structurally. It must not decide whether an execution result is trusted, promotable, or production-authoritative.

## Duplication rule

A capability, policy, validator, resource authority, or workflow must have one canonical owner. Compatibility code may adapt to that owner but must not create a second implementation of the same rule.

## Source of protected governance

Protected family governance is owned by `operations`. This public repository carries only the public-safe boundary contract.
