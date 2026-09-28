# AI Compute-Inspired Engineering Patterns

**Status:** current reusable design library.
**Purpose:** convert useful systems ideas from CPU/GPU architecture, portability layers and low-latency pipelines into repository-audit and AI-engineering patterns.
**Important:** these are engineering analogies. No hardware claim is being copied as an implementation requirement.

## 1. Pattern matrix

| Pattern | Inspiration | Project translation | Primary use |
|---|---|---|---|
| P01 Work Director | Intel Thread Director | telemetry-driven AI task/lane placement | audit scheduling, issue triage, benchmark orchestration |
| P02 Cross-Fire Mesh | AMD CrossFire | independent execution lanes with cross-checking | project-wide audits and parallel diagnosis |
| P03 Sparse Context Access | ReBAR / Smart Access Memory | direct indexed retrieval of only needed context | token efficiency and scan speed |
| P04 Capability Negotiation | FSR/XeSS portability | capability matrix + adapter/fallback rather than vendor-specific assumptions | providers, tools, languages, extraction |
| P05 Latency Guard | NVIDIA Reflex | phase-level latency measurement and shallow queues | chatbot, Actions, audits |
| P06 Shared Evidence Fabric | NVLink-style shared memory concept | explicit shared evidence/artifact references with ownership and lineage | cross-repo/project synchronization |
| P07 Compatibility Profiles | GPU driver/application profiles | bounded per-provider/per-site/per-repository quirks | extractor, provider, workflow compatibility |
| P08 Blind Differential | blind hardware/software testing | hide lane/implementation identity where possible | benchmark and cross-language audits |
| P09 Fallback Ladder | DLSS/FSR/XeSS/driver fallback | capability-ranked, policy-gated fallback | chatbot/provider/extraction recovery |
| P10 Shim/Sidecar | interception/overlay tools | add capability around a stable authority without replacing it | edge adapters and audit instrumentation |

## 2. P01 — Work Director

### Idea
Thread Director observes runtime characteristics and provides feedback so the OS can place work on an appropriate core; the project analogue is an AI Work Director that assigns audit/engineering jobs from current telemetry rather than static ticket order. Intel describes this as runtime monitoring and dynamic guidance for workload placement. [Intel](https://www.intel.com/content/www/us/en/gaming/resources/how-hybrid-design-works.html)

### Generic task descriptor
Every work item should be representable as:
`task_id, owner, feature, mutation_surface, dependencies, expected_cost, deadline, evidence_tier, lane_role, retrieval_budget, current_state, priority`.

### Scheduling logic
1. Reject tasks whose owner or dependency cannot be resolved.
2. Prefer tasks whose dependencies are ready and whose mutation surface is isolated.
3. Dispatch read-only tasks to available independent lanes.
4. Use evidence tier and deadline to avoid wasting deep runtime work on source-level questions.
5. Work-steal from blocked lanes.
6. Re-measure actual duration and retrieval cost after completion.

### Project benefit
Changes scheduling from `oldest issue first` to `highest information gain per unit of time/token` while preserving acceptance dependencies.

## 3. P02 — Cross-Fire Mesh

AMD documents CrossFire as multi-GPU rendering in which application/driver support determines whether multi-GPU work is useful and different GPUs can perform alternate-frame work. The project translation is not multi-GPU rendering; it is independent analytical lanes that test the same contract from different boundaries. [AMD](https://www.amd.com/en/resources/support-articles/faqs/DH-018.html)

Required rule: two lanes that merely repeat the same search are not independent.

Best four-lane topology:
`forward | reverse | contract-first | evidence-first`.

For six+ lanes, add policy-to-side-effect and side-effect-to-evidence lanes only when boundaries stay disjoint.

## 4. P03 — Sparse Context Access

Resizable BAR lets the CPU address a larger GPU BAR window instead of relying on small windows. Intel describes it as a PCIe capability that can improve resource access. [Intel](https://www.intel.com/content/www/us/en/support/articles/000090831/graphics.html)

Project translation: do not repeatedly load whole repositories or giant logs. Resolve a graph index first, then fetch only the relevant feature -> function -> policy -> evidence slice.

Required retrieval order:
`AI_PROJECT_MAP -> owner -> feature -> symbols -> consumers/tests -> policy -> evidence`.

Measure:
`bytes retrieved, tool calls, duplicate context, time-to-first-definitive-finding`.

## 5. P04 — Capability Negotiation

AMD's FSR is open-source and cross-platform; modern FSR integrations expose explicit inputs and pipeline stages. OptiScaler demonstrates a practical compatibility layer that can switch among multiple upscaling backends rather than hard-coding one vendor path. [AMD GPUOpen](https://gpuopen.com/fidelityfx-superresolution/); [OptiScaler](https://github.com/optiscaler/OptiScaler/blob/master/Features.md)

Project translation: every provider/tool/language should expose capabilities such as:
`structured_output, streaming, context_limit, max_output, cost_status, privacy_class, deadline_support, retryability, artifact_support`.

The router selects by capability and policy, not by vendor name.

## 6. P05 — Latency Guard

NVIDIA Reflex synchronizes the rendering pipeline and can expose measurement markers for latency debugging. [NVIDIA](https://developer.nvidia.com/performance-rendering-tools/reflex)

Project translation: measure pipeline phases separately:
`queue_wait -> retrieval -> planning -> provider_wait -> execution -> persistence -> publication -> response`.

Never optimize total runtime while ignoring queue wait or repeated retrieval. Record p50/p95/p99 and the phase responsible for the tail.

## 7. P06 — Shared Evidence Fabric

Use an explicit artifact/receipt reference graph when multiple repos need the same evidence:
`artifact_id -> producer -> revision -> owner -> consumers -> evidence_tier -> retention`.

Repositories may share evidence references without sharing private implementation authority.

## 8. P07 — Compatibility Profiles

GPU drivers historically use application-specific profiles and compatibility behavior. The safe project analogue is a bounded, versioned profile for known provider/site/workflow quirks.

Profile fields:
`target, version_range, trigger, workaround, expected_effect, regression_test, expiry, owner`.

Profiles must never silently override a canonical policy.

## 9. P08 — Blind Differential

When comparing implementations, hide implementation identity from the evaluator when practical. Compare normalized outputs, failure classes, latency and resource use before revealing which lane produced which output.

Use especially for cross-language migration and provider evaluation to reduce confirmation bias.

## 10. P09 — Fallback Ladder

Fallback should be capability-ranked and policy-gated:
`preferred -> alternate -> degraded -> blocked`.

Every transition records why the previous option was rejected. A fallback can never bypass auth, cost, privacy or evidence policy.

## 11. P10 — Shim / Sidecar

Keep the canonical authority stable while adding observability or compatibility around it. Example: `operations-edge` delegates to `operations` rather than becoming a second control plane.

Shims must be thin, bounded and non-authoritative.

## 12. What not to copy

Do not copy hardware-specific implementation claims into the software architecture.
Do not treat a consumer GPU feature as evidence that a similar software mechanism is correct.
Do not turn every analogy into production code.
Do not create another issue for every pattern; extend the existing audit/architecture trackers.

## 13. Implementation status in this project

| Pattern | Status |
|---|---|
| Work Director | documented + incorporated into audit scheduling contract |
| Cross-Fire Mesh | implemented in audit system |
| Sparse Context Access | implemented as map-first retrieval rule |
| Capability Negotiation | incorporated into provider/language audit model |
| Latency Guard | incorporated as audit/benchmark measurement rule |
| Shared Evidence Fabric | incorporated into AI map connection/evidence graph |
| Compatibility Profiles | documented as bounded profile pattern |
| Blind Differential | incorporated into cross-language/benchmark audit |
| Fallback Ladder | already present in provider/extraction policy; standardized here |
| Shim/Sidecar | incorporated into service-boundary architecture rules |

## 14. Success metrics
Track these over future audits:
`time_to_first_finding`, `time_to_root_cause`, `tool_calls_per_finding`, `retrieved_bytes_per_finding`, `duplicate_finding_rate`, `lane_overlap_rate`, `false_positive_rate`, `rework_rate`, `queue_wait_p95`, `evidence_gap_rate`.

These are measurements, not assumptions. A future benchmark should compare the old audit process against the map-first/AI-Brain process on the same frozen repository snapshots.

## 15. External research
- AMD CrossFire overview: https://www.amd.com/en/resources/support-articles/faqs/DH-018.html
- Intel Thread Director: https://www.intel.com/content/www/us/en/gaming/resources/how-hybrid-design-works.html
- Intel Resizable BAR: https://www.intel.com/content/www/us/en/support/articles/000090831/graphics.html
- NVIDIA Reflex: https://developer.nvidia.com/performance-rendering-tools/reflex
- AMD GPUOpen FSR: https://gpuopen.com/fidelityfx-superresolution/
- AMD FSR SDK: https://gpuopen.com/amd-fsr-sdk/
- OptiScaler: https://github.com/optiscaler/OptiScaler
- GitHub reusable workflows: https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows
- GitHub dependency review: https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-review