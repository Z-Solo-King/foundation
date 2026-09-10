# Phase 0: Repository Consolidation Audit

## Executive Summary

This document records the identification and removal of duplicate `payload/backend/` tree that is identical to `backend/`.

**Decision**: DELETE `/payload/` directory entirely. `/backend/` is the canonical implementation.

---

## Duplicate Verification

All Python modules in `payload/backend/` match `backend/` byte-for-byte (same BlobSha):

| Module | BlobSha | Status |
|--------|---------|--------|
| `health/check.py` | `8d9cdab6...` | ✅ Identical |
| `intelligence/sources.py` | `a5b1d90...` | ✅ Identical |
| `intelligence/planning.py` | `9e12d63...` | ✅ Identical |
| `execution/acquisition.py` | `a4bfb4c...` | ✅ Identical |
| `intelligence/claims.py` | `2cfd083...` | ✅ Identical |
| `execution/pipeline.py` | `fa00de2...` | ✅ Identical |
| `execution/resources.py` | `f8e5b0c...` | ✅ Identical |
| `intelligence/certificates.py` | `670c69e...` | ✅ Identical |
| `intelligence/contradiction.py` | `f22cb6d...` | ✅ Identical |
| `intelligence/evidence_graph.py` | `adc5d93...` | ✅ Identical |
| `execution/providers.py` | `d7a36fb...` | ✅ Identical |
| `intelligence/lineage.py` | `26534884...` | ✅ Identical |

---

## Directory Structure

**Canonical tree** (preserved):
```
backend/
├── __init__.py
├── api.py
├── main.py
├── claims.py
├── evidence.py
├── evidence_certificate.py
├── planner.py
├── relationships.py
├── research.py
├── runtime.py
├── source_lineage.py
├── content_integrity.py
├── api/
├── artifacts/
├── capabilities/
├── core/
├── evaluation/
├── execution/
├── frontend/
├── health/
├── intelligence/
├── learning/
├── models/
├── persistence/
└── sources/
```

**Duplicate tree** (to be deleted):
```
payload/
├── backend/          [DUPLICATE - delete entire]
│   └── [mirrored backend/ structure]
└── tests/            [ANALYZE]
```

---

## Pre-deletion Verification Checklist

- [ ] Confirm no imports reference `payload.backend` or `from payload`
- [ ] Confirm no test files import from `payload/`
- [ ] Confirm `pytest.ini` lists only `tests/` directory
- [ ] Confirm `conftest.py` imports from `backend/` not `payload/`
- [ ] Run existing test suite against canonical `backend/`
- [ ] Document any references in scripts or CI configs

---

## Deletion Plan

1. **Search for references** to `payload` in codebase
2. **Run tests** against current canonical `backend/` to ensure baseline passes
3. **Delete `/payload/` directory** entirely
4. **Re-run tests** to confirm no breakage
5. **Commit** with message: `Phase 0: Remove duplicate payload/backend directory; backend is canonical`

---

## Expected Impact

- **Zero functional change**: All business logic remains in canonical `backend/`
- **Reduced maintenance risk**: No more drift between parallel trees
- **Clearer architecture**: Single canonical owner for each behavior
- **Cleaner imports**: No ambiguity about which path to use

---

## Rollback

If any unexpected breakage occurs:
```bash
git revert <commit-sha>
```

No manual state repairs needed; deletion is purely file-system cleanup.
