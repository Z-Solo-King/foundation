# Migration Factory — CrossFire Execution Contract (2026-10-02)

The project needs to convert candidate evidence into actual ownership transfer. The evidence matrix requires parity, repeats, resource measurements, security/policy/provenance, shadow, canary and rollback, while explicitly treating registry presence as non-authoritative. fileciteturn0file4L9-L18 fileciteturn0file4L494-L500

## Six parallel lanes

1. runtime-frontier
2. dependency-frontier
3. tooling-ci
4. tests-benchmarks
5. target-language
6. retirement-readiness

Each lane scans the full Python surface of both repositories. The six results are independent evidence; aggregation only checks coverage/completeness. This extends the existing P1-P5 parallel model rather than creating another authority. fileciteturn0file5L120-L137

## Core rule

The state transition is:

PYTHON_AUTHORITY -> CANDIDATE -> PARITY -> RUNTIME -> SECURITY/POLICY/PROVENANCE -> SHADOW -> CANARY -> PROMOTED -> PYTHON_ROLLBACK_ONLY -> PYTHON_RETIRED -> DELETED

The current reality check says production consumer redirection and an explicit authority-transfer record are required before leaving Python authority. fileciteturn0file7L43-L57

## Target ownership

TypeScript is for public edge, HTTP/SSE, browser and search/provider boundaries; Rust is for deterministic parsing/normalization/canonicalization and CPU-bound kernels; Go is for separately justified high-concurrency boundaries; Python is retained only where an explicit protected authority still exists until independently migrated. fileciteturn0file7L34-L39

## Coverage rule

Every Python file receives exactly one disposition:

- MIGRATE
- RETAIN
- DELETE
- FOLLOW (tests/benchmarks)
- ARCHIVE

No unclassified Python is allowed.

## AI CrossFire

Deterministic repository cross-fire is implemented in CI now. Up to six external AI providers can be added as advisory reviewers when credential-backed endpoints are available. Suggested slots are OpenAI, Gemini, Groq, DeepSeek, Qwen/GLM and Kimi.

AI output remains advisory:
- it cannot promote code;
- it cannot override security/policy/provenance gates;
- disagreements become review findings;
- deterministic repository evidence remains canonical.

The current GitHub connector does not expose credential-backed external model execution as a callable tool, so this session does not claim that six external AI APIs were actually run.

## First promotion wave

Do not add new language experiments. Use already-qualified candidates:
- Rust text normalization
- Rust URL identity
- Rust JSON-LD product
- Rust HTML kernel
- TypeScript observation contract
- TypeScript public endpoint/edge boundaries

The matrix already shows strong parity/evidence for several while authority_promotion remains false. fileciteturn0file4L110-L150 fileciteturn0file4L198-L239 fileciteturn0file4L330-L379

## CI migration

Foundation's required PR workflow still uses Python CodeQL and installs/runs pytest plus Python validation tools. Therefore the tooling/CI lane must migrate verification with the production responsibility; otherwise Python remains structurally required even when runtime code has moved. fileciteturn0file1L19-L34 fileciteturn0file1L75-L117

The Foundation package also has a Python-heavy development toolchain, so removal of those dev dependencies must be tracked. fileciteturn0file0L15-L24

## Exit criteria

Migration is complete only when all production responsibilities have an explicit disposition, all promoted candidates have a bounded rollback-only period that has expired, migrated consumers no longer route through Python, obsolete Python files/imports/packages/workflows are removed, tests/benchmarks follow the production owner, and a fresh cross-repo scan reports zero unclassified Python.
