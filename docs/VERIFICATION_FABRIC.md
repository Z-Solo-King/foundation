# Verification Fabric

The project uses a reusable deterministic verification fabric across Foundation and the private Operations repository.

## Crossfire model

Every verification plan carries six orthogonal lanes:

1. structure — ownership, topology, duplicate authorities, shadow surfaces
2. contract — schemas, APIs, types and compatibility boundaries
3. behavior — tests and deterministic runtime behavior
4. security — credentials, trust boundaries and adversarial cases
5. operational — budgets, retries, checkpoints, concurrency and provider/runtime reliability
6. reconciliation — cross-repository drift, documentation drift and workflow overlap

These are analysis roles, not six independent authorities. AI may be attached as advisory evidence, but it cannot promote itself into policy or product truth.

## Where it runs

The fabric runs on trusted pushes to main, every six hours, and manual dispatch. Because it reads the private Operations repository with a read-only GitHub App credential, it is a privileged audit workflow and intentionally does not run from untrusted pull-request code. Pull requests retain the existing required verification gates; the fabric provides additional cross-repository evidence on trusted revisions.

Operations remains free of GitHub Actions. Foundation remains the workflow authority.

## Promotion rules

Critical findings block the fabric. Warnings require review and produce evidence. The scanner never mutates credentials, protected policy, production releases, or Cloudflare configuration.

## Extraction relationship

The extractor-specific six-lane crossfire remains domain-specific. The project-wide fabric supplies the higher-level verification lanes around it. Extraction still uses explicit deterministic surface evidence: HTML, JSON-LD, embedded state, REST/GraphQL/XHR, sitemap/robots, feeds, pagination, variants, price/stock, images and browser escalation.

## Evolution rule

When a new capability is added:

- add its domain classification
- map it to an existing canonical workflow
- add at least one deterministic regression test
- add a documented owner/boundary
- avoid creating a new workflow when an existing workflow family can be extended

## Release-publication verification — 2026-10-02

The verification fabric treats GitHub Release publication as a privileged boundary. Feed outputs stay workflow artifacts, and release/tag publication primitives are rejected by deterministic policy before merge.

## Final WooCommerce recovery workflow — 2026-10-02

The final least-tried WooCommerce recovery is a privileged Foundation workflow because it uses the read-only Operations GitHub App and provider credentials. It is restricted to workflow_dispatch and trusted main pushes and is registered in docs/WORKFLOW_AUTHORITY_REGISTRY.json. The workflow produces evidence artifacts only; it does not publish retailer feed URLs as releases.

## Migration Factory CrossFire — 2026-10-02

The Migration Factory workflow extends the verification fabric with six read-only migration lenses: runtime frontier, dependency frontier, tooling/CI, tests/benchmarks, target-language disposition, and retirement readiness. On trusted Foundation revisions it audits an immutable Operations SHA and produces independent evidence without changing production authority.

## Nightly workflow duplicate reconciliation — 2026-10-02

The canonical 24-program nightly workflow was restored to the last known-good single-definition revision after a duplicated merge artifact produced repeated job identifiers and invalid YAML. The workflow now contains one production_gate, one research, one migration_review, one project-summary, and one final-gate. Subsequent changes must modify that canonical workflow rather than append duplicate job blocks.

## Node tooling migration — public-core synchronization

The public-core synchronizer was migrated from Python to Node as repository tooling. Foundation-owned validation now executes its Node contract test; the migration does not change public/runtime authority or the immutable Foundation core pin.

## 2026-10-02 Migration Factory token-step correction

The trusted-main Migration Factory resolve job has one canonical read-only Operations GitHub App token step. Duplicate token-step definitions are prohibited because they can create conflicting step identifiers and violate the single-provider-credential boundary. The workflow remains trusted-main/manual-only and private Operations access remains contents:read.

## Node tooling migration — nightly/runtime gates — 2026-10-02

Foundation-only nightly runtime probing, loopback research transport, GitHub Actions zero-cost validation, and benchmark-finding publication now execute through Node tooling. The superseded Python scripts/tests were removed; protected Python research and governance authorities are unchanged. Workflow changes remain contract-tested and do not constitute live runtime/provider acceptance.

## Nightly dry-run ordering invariant

The canonical nightly workflow establishes Research mode before the live-only deployed-runtime verification step. An explicit dry_run=true therefore bypasses the production-release gate and the live runtime probe while remaining on the deterministic contract-testing path; production-live execution retains the existing exact-release, preflight, and evidence gates.

## Nightly benchmark AI cross-fire — 2026-10-03

The nightly benchmark now has a separate six-lane AI cross-fire advisory workflow. It runs on a trusted scheduled trigger or explicit manual dispatch, uses read-only GitHub permissions, and sends only the deterministic final benchmark receipt to six parallel Workers AI model lanes. It records transport status, latency, reported neuron usage, schema compliance, advisory assessment, and input provenance.

The cross-fire is intentionally outside the benchmark acceptance gate. AI output cannot certify benchmark correctness, research completion, production health, credentials, policy, deployment, Cloudflare state, or workflow dispatch. Invalid model formatting is recorded as schema non-compliance rather than converted into success.

The cross-fire is an observability and reasoning layer over the canonical benchmark: deterministic benchmark evidence remains authoritative, while AI disagreement and repeated flags can identify candidates for follow-up reproduction, regression coverage, or future benchmark design.

## Session-independent execution boundary — 2026-10-03

Durable automation is hosted execution. GitHub Actions schedules, trusted-main pushes, and explicit workflow dispatches are the liveness source; ChatGPT/mobile conversations and interactive connector sessions are not. Workflow artifacts and run IDs provide cross-job/run handoff.

Application `chat_id` and `request_id` values, where used, are run-scoped correlation identifiers generated from workflow/mission identity. They are not ChatGPT conversation/session identifiers. AI review remains advisory-only and cannot become scheduler, acceptance, credential, deployment, or Cloudflare mutation authority.
