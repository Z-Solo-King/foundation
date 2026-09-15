# Foundation repository instructions

Foundation is the public-safe contract, deterministic research core and public Worker/API repository.

## Before changing code
1. Read `REPOSITORY_MAP.json` and the relevant ownership document.
2. Search both active repositories for an existing implementation.
3. Extend the canonical owner instead of creating a duplicate.
4. Keep public/private boundaries intact.
5. Add focused regression tests for behavior changes.

## Code and evidence
- Keep deterministic logic independent from transport and persistence where practical.
- Preserve unknown, blocked, contradictory, stale, partial and inferred states.
- Do not turn network failures into successful empty results.
- Keep public code free of private credentials, protected policy and private runtime details.

## Family ownership
- Foundation owns public-safe contracts, deterministic evidence/intelligence primitives, planning, and the public Worker/API boundary.
- Operations owns protected policy, resource governance, private acquisition/execution, evaluation, promotion, rollback/recovery, deployment/recovery and chatbot control.
- Shared behavior uses the Foundation public contract/package; do not copy implementation across repositories.

## Validation
Run the repository tests and boundary checks. For cross-repository changes, inspect the corresponding owner repository before changing the public contract.
