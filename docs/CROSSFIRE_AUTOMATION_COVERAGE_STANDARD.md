# CrossFire Automation Coverage Standard

**Status:** normative

This standard applies repository-wide to automation, scanning, audit, migration, extraction, runtime reconciliation, and governance.

## Core pattern

1. Observe bounded inputs.
2. Run independent lanes in parallel when the work benefits from independent lenses.
3. Normalize results into structured evidence.
4. Preserve disagreement and classify failures/timeouts.
5. Resolve against the existing canonical deterministic/policy authority.
6. Perform stateful writes, merges, promotion, or issue mutation only after evidence collection and the existing authority gate.

CrossFire is **not** majority voting and is not an alternative authority.

## Six deterministic lenses

The default engineering scan lenses are structure, boundary, runtime, security, quality, and provenance. A component may specialize the lens objective, but it must preserve independence and explicit evidence semantics.

## AI/API lanes

AI provider cross-fire is adaptive: 0/2/4/6 lanes depending on ambiguity, expected evidence gain, and a dedicated resource budget. Six is the target and five successful independent lanes is the strong comparative threshold. AI lanes receive the same bounded approved input and do not receive another lane answer during the evidence phase.

The canonical provider runtime remains responsible for provider eligibility, quota, privacy, retry, cost, and model selection. AI outputs are advisory and require deterministic or policy verification before becoming actionable.

## Coverage gate

`tools/crossfire_surface_audit.py` validates that every project-improvement component is covered by this CrossFire contract, its workflow references resolve, and the core automation surfaces remain present. A dedicated scheduled/push/dispatch workflow runs this gate independently of the provider credentials, so a missing or unavailable AI provider cannot hide structural coverage drift.

## Token and artifact discipline

Keep context bounded and retain hashes, lengths, outcomes, latency, normalized findings, and provenance rather than full model transcripts. Raw provider output is excluded by default. This keeps CrossFire useful at repository scale without turning evidence artifacts into an unbounded storage or token channel.
