# Phase 0 Boundary and Consolidation Audit

## Status

The duplicate `payload/backend/` tree was removed earlier in the public repository. `/backend/` remains the canonical public implementation tree.

This audit is now extended to cover the public/private trust boundary.

## Confirmed Canonical Ownership

- `backend/` is the single public application implementation tree.
- No public production promotion authority should remain here.
- Public evaluation code must contain only publishable fixtures/interfaces.

## Private-Only Responsibilities

The companion private repository owns:

- protected policy authority;
- production promotion/canary/rollback authority;
- private benchmark holdouts and expected results;
- deployment configuration contracts;
- protected security and trust decisions;
- private operational state and evidence authority.

## Boundary Findings

`backend/learning/promotion.py` was identified as authority-bearing because it could decide canary/promotion/rollback state and reject or accept protected-policy changes. That implementation has been removed from the public boundary and recreated as protected private control-plane authority.

`tests/test_promotion.py` was also removed from the public repository; promotion authority is tested privately.

## Verification Requirements Before Production

- Search public source, tests, docs and workflows for secrets, credentials, private-state paths, holdouts, protected policy, and promotion authority.
- Verify public code exposes only data contracts/interfaces where a private decision is required.
- Verify private code is not imported by public runtime code.
- Verify public workers never receive private evidence/state or private evaluation answers.
- Run public and private test suites independently.
- Treat passing public tests as necessary but insufficient for production readiness.

## Rollback

All changes were made on dedicated Phase 0 branches. Revert the corresponding commit(s) if validation uncovers a compatibility problem.
