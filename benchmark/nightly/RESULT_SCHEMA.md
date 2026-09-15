# Nightly result contract

Every experiment record must distinguish:

- `observation`: what the runner actually observed;
- `confirmed_defect`: reproducible failure with deterministic reproduction;
- `hypothesis`: plausible but unverified explanation;
- `improvement_candidate`: proposed change awaiting validation;
- `blocked_external_dependency`: required capability/source was unavailable;
- `obsolete_assumption`: prior assumption disproved by current evidence.

A result is never accepted as project evidence merely because an LLM produced it. External claims require source receipts; model output remains candidate-only until verified by the canonical evidence pipeline. Chat feedback remains candidate learning and cannot overwrite identity, evidence, policy, security, billing, access control, or resource limits.

Metrics should include wall-clock latency, agent-seconds, input/output/cached/thinking tokens when exposed, tool calls and useful-call ratio, duplicate work, context peak, evidence gain, source diversity, contradiction state, and final quality. Missing metrics are recorded as missing, not zero.
