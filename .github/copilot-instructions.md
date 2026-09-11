# Foundation repository instructions

## Role
Foundation is the public-safe contract and research-primitives repository in the Z-Solo-King family.

Own here: public-safe contracts, deterministic evidence/intelligence primitives, planning, API boundary, bounded public-worker behavior.
Do not move private provider secrets, private policy authority, protected evaluation holdouts, heavy extraction, or heavy product mapping here.

## Before changing code
1. Search the family architecture and source-of-truth map.
2. Search for existing implementations before adding a class/function/policy/DTO.
3. Prefer one canonical implementation plus a thin compatibility facade when legacy imports require it.
4. Preserve public/private boundaries.
5. Add deterministic and regression tests for behavioral changes.

## Correctness
- Preserve explicit uncertainty and contradictions.
- Validate hashes, provenance, schemas, budgets, replay state, and public-worker outputs at boundaries.
- Do not infer that an HTTP/network failure is an empty successful result.
- Keep deterministic code paths cheap: bounded work, indexed lookups, small immutable contracts.

## Family ownership
- Operations owns protected policy, global resource governance, evaluation, promotion, rollback, and chatbot control-plane policy.
- Extractor-mapper owns acquisition, extraction, mapping, and heavy legacy engines.
- Cross-repository duplication is a design defect unless it is a documented compatibility boundary.

## Validation
Run the repository tests and boundary checks. For cross-family changes, inspect the corresponding owner repository before duplicating logic.
