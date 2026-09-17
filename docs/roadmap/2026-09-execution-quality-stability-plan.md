# Heroic AI — Execution, Quality, Stability & Efficiency Roadmap

Status: planning baseline

This document records the implementation backlog for the next capability layer. It does not certify production/L4 behavior. Foundation remains the public contract/evidence boundary; Operations remains the private runtime/policy/resource authority.

## Workstreams

1. Adaptive execution and parent budgets — Operations #329, #330
2. Resilience, retries, cancellation, admission and fairness — Operations #331, #333
3. Cache/coalescing and provider intelligence — Operations #332, #334
4. Research answer completeness and evidence verification — Foundation #385, #386
5. Performance, useful-output efficiency and regression gates — Foundation #387, #388
6. Reproducibility and provenance — Foundation #389

## Additional acceptance work

- Real-source/oracle evaluation and adversarial validation.
- L3 GitHub CI evidence must remain distinct from approved private-runtime/L4 evidence.
- Runtime acceptance for Operations #119, #120, #132, #145, #155, #164, #181 and #197 remains required where applicable.
- B2 disaster-recovery certification remains separate from repository-level evidence.
- Production authentication, bindings, secrets, provider eligibility and resource authority must not be weakened or invented.

## Implementation order

P0: establish budgets/amplification control; adaptive lanes and research stop conditions; claim/evidence verification and completeness; latency decomposition; retry/cancellation/circuit-breaker behavior; admission/backpressure.

P1: cache/coalescing; provider health/capacity intelligence; continuous adversarial evaluation; provenance/replay identity; quality/performance release gates.

P2: marginal-value research optimization, capacity forecasting refinements, controlled self-healing and broader automated sampling only after P0/P1 evidence is stable.

## Non-goals

- No autonomous unbounded agents.
- No second resource authority, database, or deployment owner.
- No direct feedback-to-policy promotion.
- No claim that repository tests prove Cloudflare/private-runtime production behavior.
