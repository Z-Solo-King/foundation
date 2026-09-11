# Family engineering guidance

Read `AI_CODEMAP.json` and `docs/FAMILY_ARCHITECTURE.md` before changing architecture.

Foundation owns public-safe contracts, deterministic research/evidence primitives, planning, and the public worker boundary.
Operations owns protected policy, resources, evaluation, promotion, rollback, and chatbot control-plane authority.
Extractor-mapper owns acquisition, extraction, mapping, adapters, and heavy legacy engines.

Before adding code, search all family repositories for an existing implementation and identify its canonical owner. Prefer a compatibility facade over a second implementation when legacy imports must remain.

Never expose private topology, secrets, evaluation holdouts, or protected implementation through this public repository.
