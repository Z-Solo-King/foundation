# Family engineering guidance

Read `AI_CODEMAP.json` and `docs/FAMILY_CONTRACT.json` before changing architecture. Read `docs/FAMILY_ARCHITECTURE.md` when a change crosses the repository boundary.

Foundation owns public-safe contracts, deterministic research/evidence primitives, planning, and the public Worker/API boundary. Operations owns protected policy, resources, private acquisition/execution, evaluation, promotion, rollback, deployment/recovery, and chatbot control-plane authority. The retired `extractor-mapper` repository is historical archive material only and is never an active owner.

The canonical family ownership contract is `docs/FAMILY_CONTRACT.json`; do not create a competing family policy document elsewhere. Local repositories may document repository-specific implementation guidance, but may not redefine family ownership.

Before adding code, search both active family repositories and identify the canonical owner. Extend the owner rather than creating a second implementation. Prefer a compatibility facade over duplicated logic when legacy imports must remain.

Cross-repository changes follow dependency direction: Foundation contract/core first, Operations consumer/control-plane integration second. Keep one coherent feature branch and one PR per owning repository. Do not use synchronized copy-paste commits where a contract or canonical package can be consumed instead.

Code should remain easy for humans and AI to navigate: use explicit typed boundaries, concise module docstrings, local invariants, deterministic error semantics, bounded side effects, small cohesive modules, and owner/boundary tests. Do not create a convenient top-level module when an existing owning package already exists.

Never expose private topology, secrets, evaluation holdouts, or protected implementation through this public repository.
