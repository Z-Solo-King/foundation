# Unified Scan / Monitor / CrossFire Composition

## Canonical systems reused

- tools/verification_fabric.mjs — deterministic verification scanner and workflow planner.
- tools/multi_lens_planner.mjs — adaptive scheduling-only lane planner.
- tools/autonomous_mission_router.mjs — mission constraints and allowlisted workflow routing.
- tools/autonomous_engineering_supervisor.mjs — bounded remediation supervisor.
- tools/comprehensive_governance_scan.py — eight-domain governance observation lanes.
- .github/workflows/exhaustive-six-lane-audit.yml — six concurrent audit lanes.
- .github/workflows/polyglot-governance-audit.yml — strict language/file coverage.
- .github/workflows/live-ai-provider-crossfire.yml — up to six independent AI/provider API lanes.

No replacement scanner or second scheduler is introduced.

## Combined execution model

1. Map-first retrieval resolves owners, canonical paths, policies, tests, workflows and live evidence references.
2. A shared immutable revision snapshot and inventory are created once.
3. The adaptive multi-lens planner partitions work by risk, expected information gain and cost.
4. Fast breadth checks establish coverage before expensive analysis.
5. Six evidence lenses run independently where they add information: TypeScript breadth, Rust quality, Go fan-out, security, Cloudflare/runtime and policy/reconciliation.
6. Existing domain scanners are invoked as detectors inside those lanes instead of being copied.
7. Live runtime/provider checks are joined only where the claim requires them.
8. The existing six-provider AI CrossFire runs as a separate advisory evidence layer; five independent successful lanes is the strong threshold and unavailable providers are recorded as limitations.
9. Deterministic reconciliation compares normalized invariants, evidence references, revision identity and disagreements.
10. One receipt becomes the input to monitors, dashboards and bounded autonomous remediation.

## CrossFire meaning

The language/evidence lenses and the AI/provider lanes are two different dimensions of independence. Running six languages is not the same as running six APIs, and six APIs are not six votes. Independence means materially different evidence paths against the same bounded input.

## Parallelism

Read-only scans, benchmarks, provider calls and independent audit lanes may run concurrently within resource budgets. Stateful writes are serialized and authority-owned. A failed lane is classified as execution failure, not silently treated as a clean result.

## Coverage gate

Completion requires every tracked item to have an explicit disposition, every required lane to have an execution state, every critical finding to have provenance, every live claim to have runtime evidence, and every disagreement to remain visible until adjudicated by the canonical authority.

## Token/cost strategy

Use the project map and owner indexes before broad retrieval. Reuse shared artifacts instead of rereading the same repository. Send bounded structured evidence to AI providers rather than full source dumps. Measure retrieval bytes, tool calls, latency, quota and duplicate context as scheduler feedback.

## Authority boundary

AI planning, scores, benchmarks, dashboards and maps remain non-authoritative. Existing source, deterministic tests, provider runtime, resource governance, protected policy, deployment and promotion authorities remain canonical.