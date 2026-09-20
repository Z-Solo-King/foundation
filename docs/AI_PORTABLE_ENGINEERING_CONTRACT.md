# AI-Portable Engineering Contract
Last updated: 2026-09-20

This repository must remain maintainable when the coding agent or model changes.

## Core rule

Language choice is based on:
1. runtime/platform fit;
2. migration risk and sequencing;
3. measured evidence;
4. AI/tooling maintainability.

AI compatibility is a separate gate and never overrides security, policy, provenance, ownership or runtime evidence.

## Current verified project toolchains

- Python 3.14
- Node.js 22 / TypeScript
- Rust stable
- Go 1.25
- GitHub Actions on Foundation only

Other languages may be assistant-supported but are not part of the verified project default toolchain until CI proves them.

## Cross-agent portability

Repository knowledge is versioned, not hidden in model memory.

- Codex uses `AGENTS.md`.
- Claude Code uses `CLAUDE.md`.
- Gemini uses `GEMINI.md`.
- GitHub Copilot uses `.github/copilot-instructions.md` and `AGENTS.md`.

These files are thin adapters pointing to stable documentation. Business logic never depends on one agent.

## Migration invariants

Every migration leaves:
- one canonical owner;
- a language-neutral contract;
- deterministic tests;
- reproducible build/test commands;
- explicit rollback;
- security/provenance invariants;
- enough documentation for a different coding model to reproduce the change.

GitHub documents broad Copilot language support but notes that quality varies with training-data volume/diversity. Gemini Code Assist publishes a separate verified language set. Therefore assistant compatibility is evidence, not a substitute for runtime fit.

Use the runtime language scorecard, then the AI-maintainability gate, then the normal parity/benchmark/security/authority gates.

Detailed cross-family policy: see the synchronized AI portability system under Operations.
