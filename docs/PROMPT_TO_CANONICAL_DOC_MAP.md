# Prompt-to-canonical-doc map — Foundation

| Task | Canonical source |
|---|---|
| Ownership / placement | AGENTS.md, REPOSITORY_MAP.json, docs/FAMILY_ARCHITECTURE.md |
| Current family state | docs/CURRENT_SOURCE_OF_TRUTH.md |
| Audit routing | docs/AI_AUDIT_SYSTEM.md |
| Feature/function/policy navigation | docs/AI_PROJECT_MAP.json + docs/AI_PROJECT_MAP.md |
| AI provider fleet / task fabric | docs/AI_PROVIDER_FLEET_2026-09-30.json + Operations private provider/task-fabric sources |
| AI/provider/extractor synchronization | Operations tools/mapper_extractor_cross_audit.py + Foundation provider contract |
| Research acceptance | #157 + current workflow/runtime evidence |
| Feed recovery | #1247 / #1249 + current evidence |
| AI benchmark | #1157 + docs/AI_AGENT_BENCHMARK_SYSTEM.md |
| Exhaustive coverage | #58 + docs/AI_AUDIT_SYSTEM.md |

Session handoffs, chat adapters and dated observations are continuity aids only; they do not define current state.
Mutable issue/PR status is always read live from GitHub.

## AI / extractor boundary
Foundation owns public-safe contracts and workflows. Operations owns private provider/task-fabric runtime. extraction_assist remains candidate-only and cannot create evidence or mapper authority.