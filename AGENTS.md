# Family engineering guidance

Read `AI_CODEMAP.json` and `docs/FAMILY_CONTRACT.json` before changing architecture. Read `docs/FAMILY_ARCHITECTURE.md` when a change crosses a repository boundary.

Foundation owns public-safe contracts, deterministic research/evidence primitives, planning, and the public worker/API boundary. Operations owns protected policy, resources, evaluation, promotion, rollback, and chatbot control-plane authority. Extractor-mapper owns acquisition, extraction, mapping, adapters, and heavy bounded execution.

The canonical family ownership contract is `docs/FAMILY_CONTRACT.json`; do not create a competing family policy document elsewhere. Local repositories may document their private or execution-specific extensions, but not redefine family ownership.

Before adding code, search all family repositories for an existing implementation and identify its canonical owner. Prefer a compatibility facade over a second implementation when legacy imports must remain.

Cross-repository changes use dependency order: contract first, implementation second, protected control-plane integration last. Keep one coherent feature branch and one PR per owning repository.

Never expose private topology, secrets, evaluation holdouts, or protected implementation through this public repository.
