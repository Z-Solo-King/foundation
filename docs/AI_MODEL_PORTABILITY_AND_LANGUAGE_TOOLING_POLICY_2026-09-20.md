# AI-Model Portability and Language Tooling Policy

**Status:** migration guardrail; no production authority change
**Date:** 2026-09-20

## Objective

Keep the codebase maintainable when switching between coding agents, model providers, IDEs, or execution environments. The repository must not depend on one model's private assumptions, generated style, or tool-specific workflow.

## Supported baseline languages

| Language | Default role | Portability posture | Promotion requirement |
|---|---|---|---|
| Python | policy, orchestration, governance, persistence, provenance, semantic authority | primary reference implementation | retain unless measured replacement passes all authority gates |
| TypeScript | edge HTTP, browser, SSE, adapters, typed contracts | first-class migration language | strict typecheck, deterministic tests, browser/runtime contract tests |
| Rust | bounded pure CPU kernels, normalization, hashing, dedupe | candidate language, not default | benchmark whole boundary including conversion/FFI overhead |
| Go | independently scalable concurrent service only | conditional | explicit service boundary, load profile, operational ownership and rollback plan |
| JavaScript | compatibility only where runtime requires it | avoid new core logic when TypeScript is viable | no new untyped authority without documented exception |
| PHP | WordPress/PHP ecosystem boundary only | isolated adapter | integration contract and dependency lockfile |
| Java/.NET/C++/Zig | specialized external/library/platform need only | deferred by default | concrete capability gap plus ownership and CI evidence |

## AI-model portability requirements

Every migrated component must include:

1. A short responsibility statement and explicit non-responsibilities.
2. A language-independent input/output contract with versioned examples.
3. Deterministic fixtures, including negative and boundary cases.
4. A command-line or test entry point that does not require a particular AI agent.
5. Reproducible formatting, linting, typechecking, and test commands.
6. No hidden dependence on model-generated files, undocumented prompts, or IDE state.
7. A migration note describing how to replace the implementation in another language.
8. Explicit ownership for policy, security, provenance, persistence, replay, and rollback.

## Agent compatibility score

The language/component score must separately assess:

- compiler/interpreter availability in the supported CI image;
- formatter, linter, type checker, debugger, and test runner availability;
- quality of diagnostics exposed to coding agents;
- repository search/index support;
- availability of stable language-server tooling;
- dependency lockfile and reproducible build support;
- ease of writing deterministic fixtures;
- quality of cross-language contract tooling;
- number of special runtime assumptions;
- migration and rollback cost.

This is an engineering maintainability score, not a claim that every AI model supports every language equally. Models can produce syntax for many languages, but reliability depends on repository context, tool access, compiler feedback, tests, and the model's ability to inspect the actual project.

## Hard portability gates

A component is not migration-ready merely because an agent can generate code or a compiler accepts it. The following are mandatory:

- exact behavioral parity against the reference implementation;
- security and policy parity;
- provenance and observability parity;
- deterministic replay and failure classification;
- at least 32 orthogonal benchmark cases with 3 repeats;
- documented p50/p95/p99 and memory results where performance is relevant;
- shadow comparison before canary;
- rollback rehearsal;
- retirement of the old path only after all consumers are redirected.

## Boundary economics

Avoid tiny cross-language calls. Batch meaningful work across Python/Rust or Python/TypeScript boundaries, and measure serialization, allocation, startup, and conversion costs as part of the complete operation. A faster kernel is not a win if boundary overhead dominates.

## AI-agent operating rules

- Prefer small, independently reviewable changes.
- Do not rewrite a large file solely because it is large.
- Do not introduce a new language without a component-level reason.
- Do not duplicate security or governance authority.
- Do not infer parity from unit tests alone.
- Keep generated artifacts reproducible and clearly marked.
- Record commands and evidence in the PR body.
- Make the code navigable through stable names, typed contracts, and concise module boundaries.
- Keep one canonical implementation per responsibility; compatibility shims must have an explicit retirement condition.

## Review checklist

- [ ] Can a different model discover the component without conversation history?
- [ ] Is the contract understandable without reading the implementation?
- [ ] Are build/test commands documented and executable in CI?
- [ ] Are failures deterministic and classified?
- [ ] Are ownership and authority boundaries explicit?
- [ ] Are migration, shadow, canary, rollback, and retirement states recorded?
- [ ] Does the change improve or preserve multi-language maintainability?
