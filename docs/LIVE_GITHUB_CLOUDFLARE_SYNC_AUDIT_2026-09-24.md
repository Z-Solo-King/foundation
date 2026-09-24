# Live GitHub + Cloudflare Sync Audit — 2026-09-24

## Current repository heads

- Foundation `main`: `3913f88eab1f6ed0ae4834f0084799662045c418`
- Operations `main`: `0e6aae23860e260bd0d5c64bc7e71284b643cddf`

## Current GitHub inventory

- Foundation open issues: 2 (`#58`, `#157`)
- Operations open issues: 6 (`#145`, `#340`, `#385`, `#597`, `#603`, `#699`)
- Foundation open PRs: `#1093`
- Operations open PRs: 0
- Total open issues: 8
- Total open PRs: 1

## Cloudflare production state

### Public Worker

- Name: `research-intelligence-engine-public`
- Active version: `435`
- Active version ID: `68b8a811-b559-4488-8950-567f911445f4`
- Allocation: 100%
- Deployment annotation: Foundation `3913f88eab1f6ed0ae4834f0084799662045c418`
- `RELEASE_FOUNDATION_SHA`: `3913f88eab1f6ed0ae4834f0084799662045c418`
- `RELEASE_OPERATIONS_REF`: `1a12b98981f52de207fa8626cf2e1f5ad06659be`
- Schedules returned: none

### Private Worker

- Name: `research-intelligence-engine-private`
- Active version: `262`
- Active version ID: `4f81aac1-241e-4af0-bdce-70683758e274`
- Allocation: 100%
- Deployment annotation: GitHub `1a12b98981f52de207fa8626cf2e1f5ad06659be`
- Schedule: `*/15 * * * *`
- D1 binding: `OPERATIONS_DB`
- Service binding: `FOUNDATION` -> public Worker
- `STRICT_ZERO_COST_ONLY`: `true`

## Research and benchmark evidence

- Latest recorded extractor benchmark: `#348`
- Benchmark evidence recorded: 40 receipts; provenance and route provenance 1.0; repeat reliability 1.0; zero unstable repeated groups
- Latest recorded nightly: `#878`
- Nightly state: provider-gated before provider execution because `RESEARCH_LLM_ENDPOINT`, `RESEARCH_LLM_API_KEY`, and `RESEARCH_LLM_MODEL` were absent
- Nightly artifact: `#10772875132`, recorded as 40 matrix cases + 24 capacity cases
- Structural/CI evidence must not be represented as L4 runtime acceptance

## Reconciliation notes

- Historical issue-body sync blocks contain older repository heads and issue counts. They remain historical evidence.
- Current deployment pins must not be changed merely to match moving `main` heads. The private Worker and public Worker use an explicit Operations revision boundary.
- Provider-backed nightly execution remains externally gated by authorized research-provider configuration.
- Runtime-only issues remain open until approved live receipts are available.
