# Family engineering guidance

Read `REPOSITORY_MAP.json` and `docs/FAMILY_CONTRACT.json` before changing architecture. Read `docs/FAMILY_ARCHITECTURE.md` when a change crosses the repository boundary.

If working from the open issue queue, also read `operations/docs/AI_AGENT_PARALLEL_TRACK_ASSIGNMENT.md` and pick up your assigned `track:*` label — it tells you which issues (in both repositories) are safe to work in parallel without file-surface collisions, which are pure runtime-evidence gates requiring no code, and which infra-blocker issues must be resolved before anything else.

Foundation owns public-safe contracts, deterministic research and evidence primitives, planning, and the public Worker/API boundary. Operations owns protected policy, resource governance, private acquisition/execution, evaluation, promotion, rollback, deployment/recovery, and chatbot control.

Before adding code, search both active repositories for an existing implementation and identify the canonical owner. Extend that owner rather than creating a second implementation. Use a thin compatibility facade only when a supported legacy import requires it.

Cross-repository changes follow dependency direction: Foundation contract/core first, Operations consumer/control-plane integration second. Do not copy implementation between repositories to avoid a dependency.

Keep code readable to another maintainer: explicit types, cohesive modules, narrow functions, clear error semantics, bounded side effects, and tests beside the owner. Avoid creating a module only because its name is convenient.

Never expose private topology, credentials, evaluation holdouts, or protected implementation through this public repository.
