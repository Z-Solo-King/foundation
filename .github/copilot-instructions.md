# Foundation repository instructions

## Role
Foundation is the public-safe contract and research-primitives repository in the Z-Solo-King family.

Own here: public-safe contracts, deterministic evidence/intelligence primitives, planning, API boundary, bounded public-worker behavior.
Do not move private provider secrets, private policy authority, protected evaluation holdouts, heavy extraction, or heavy product mapping here.

## Before changing code
1. Search the family architecture and source-of-truth map.
2. Read the continuity records before proposing new architecture, especially:
   - `docs/KNOWLEDGE_LEDGER_2026-09-13.md`
   - `docs/PLANNER_KNOWLEDGE_LEDGER_2026-09-13.md`
   - `docs/PLANNER_FEATURE_BACKLOG_2026-09-13.md`
3. Search for existing implementations before adding a class/function/policy/DTO.
4. Prefer one canonical implementation plus a thin compatibility facade when legacy imports require it.
5. Preserve public/private boundaries.
6. Add deterministic and regression tests for behavioral changes.
7. Treat the historical extractor/scraper/mapper material as engineering lineage and reusable design evidence, not a reason to recreate a third active architecture.

## Planner-first continuity rule
The planner is intentionally being designed feature-first before broad implementation. Preserve newly discovered planner capabilities, tradeoffs, rejected approaches and source-derived lessons in the versioned planner continuity records before treating the design as settled. Do not collapse the planner to a stage list when a decision, budget, fallback, stop rule, source profile, query portfolio, or execution dependency matters.

Historical extractor/mapper lessons are especially important for planner design: bounded pagination, completeness, repeated-page detection, source/method profiles, per-source pacing/concurrency, failure classification, quarantine/cooldown, structured-representation preference, deterministic identifier-first work, conflict detection, candidate recall and replayability. Generalize these as contracts rather than copying network/parser logic into the planner.

## Correctness
- Preserve explicit uncertainty and contradictions.
- Validate hashes, provenance, schemas, budgets, replay state, and public-worker outputs at boundaries.
- Do not infer that an HTTP/network failure is an empty successful result.
- Keep deterministic code paths cheap: bounded work, indexed lookups, small immutable contracts.
- Planner output proposes bounded work; it never becomes evidence authority or protected policy authority.

## Family ownership
- Operations owns protected policy, global resource governance, evaluation, promotion, rollback, and chatbot control-plane policy.
- Historical extractor-mapper material owns no new active security boundary; its useful acquisition/mapping lessons must be expressed through stable Foundation/Operations contracts where adopted.
- Cross-repository duplication is a design defect unless it is a documented compatibility boundary.

## Validation
Run the repository tests and boundary checks. For cross-family changes, inspect the corresponding owner repository before duplicating logic.
