# Foundation repository instructions

Foundation is the public-safe contract, deterministic research core and public Worker/API repository. It is also the family’s canonical GitHub Actions and production-deployment owner.

## Before changing code
1. Read `REPOSITORY_MAP.json` and the relevant ownership document.
2. Read `docs/MAINTENANCE_CONTRACT.md` first; use Operations `docs/AGENT_MAINTENANCE_GUIDE.md` for private-family maintenance.
3. Search both active repositories for an existing implementation.
4. Extend the canonical owner instead of creating a duplicate.
5. Keep public/private boundaries intact.
6. Do not create a second current-state/handoff/governance/architecture/knowledge document; extend the canonical owner.
7. Add focused regression tests for behavior changes.

## Family boundaries
- Foundation owns public-safe contracts, deterministic evidence/intelligence primitives, planning, frontend/public API and canonical GitHub Actions/deployment.
- Operations owns protected policy, resource governance, private acquisition/execution, provider/runtime selection, evaluation, promotion, rollback/recovery and chatbot control.
- Shared behavior uses the Foundation public contract/package; do not copy protected implementation across repositories.
- The retired `Z-Solo-King/extractor-mapper` repository is historical; `operations/extractor_mapper/` is the active directory in Operations.

## Code and evidence
- Keep deterministic logic independent from transport and persistence where practical.
- Preserve unknown, blocked, contradictory, stale, partial and inferred states.
- Do not turn network failures into successful empty results.
- Keep public code free of private credentials, protected policy and private runtime details.
- Distinguish source/test/CI/deployment/runtime/production evidence; never promote a lower evidence level by wording.

## Automation
- Foundation owns the family’s GitHub Actions and canonical production release path.
- Do not introduce a second deployment authority.
- Do not manually dispatch/rerun privileged workflows during repository maintenance unless explicitly required and authorized.

## Validation
Run repository tests and boundary checks. For cross-repository changes, inspect the corresponding owner repository before changing the public contract.

Use `REPOSITORY_MAP.json` as the canonical navigation map. Do not assume an `AI_CODEMAP.json` exists unless it is actually present in the current tree.
