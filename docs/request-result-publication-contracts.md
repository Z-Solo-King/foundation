# Research request, result and publication contracts

Version: `research-contracts/v1`

Related issues: #410, #409, #412, #414, #415.

## Research request

A request should be normalized into an immutable execution contract containing the objective/subquestions, required and optional scope, freshness/temporal requirements, evidence/citation requirements, allowed tool/source classes, deadline, budget envelope and publication/privacy constraints.

Retries reference the same request contract. They cannot silently relax freshness, evidence or resource requirements.

## Execution states

Use explicit state semantics where the capability requires them:

`QUEUED` → `RUNNING` → one of `COMPLETED`, `PARTIAL`, `DEGRADED`, `BLOCKED`, `FAILED`, `CANCELLED`, `UNSUPPORTED`.

A provider finishing normally does not imply answer-level completion. Budget exhaustion, policy denial, unsupported capability, timeout and cancellation remain distinguishable outcomes.

## Publication gate

A result is publication-eligible only after composition of the canonical state/evidence controls for the request. The gate considers:
- execution terminal state;
- requested/completed/missing/failed scope;
- claim support state;
- source/evidence integrity and independence;
- freshness compliance;
- contradiction state;
- provenance completeness;
- public/private disclosure eligibility.

`COMPLETED` is therefore necessary in relevant paths but is not, by itself, sufficient for public publication.

## Authority boundaries

This document composes existing authorities. It does not introduce another resource ledger, evidence evaluator, memory store, provider selector or publication policy owner.

The public result must expose only public-safe contract fields. Private routing/provider/resource details remain behind the approved boundary.

## Negative cases

Required fixtures include partial execution presented as success, stale-but-supported evidence, cited-but-unsupported claims, policy-blocked completion, exhausted budgets, cancelled work, incompatible contract versions and private evidence leaking into a public artifact.
