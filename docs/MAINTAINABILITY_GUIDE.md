# Maintainability Guide

This guide keeps the public Foundation repository easy to change safely.

## Ownership

Foundation owns public-safe contracts, evidence structures and deterministic research primitives. Operations owns private policy, resource governance, credentials, private acquisition/execution, evaluation, promotion and chatbot control.

A compatibility module may preserve an older import path, but it must not become a second implementation.

## Code structure

Keep modules cohesive and keep transport thin. Separate deterministic logic from I/O, policy from execution, and persistence from domain semantics. Prefer explicit types and narrow functions over clever abstractions.

Every non-trivial module should make its purpose clear and document important invariants or failure behavior. Comments should explain why a constraint or fallback exists rather than restating the code.

## Evidence and boundaries

Keep unknown, blocked, contradictory, stale, partial and inferred states distinct. Do not turn model output or private runtime state into public authority. Foundation must never import Operations implementation details or private credentials.

## Documentation

Use `REPOSITORY_MAP.json` for ownership and navigation. Keep canonical documents current and mark dated material as historical. Repository state and fresh execution evidence take precedence over old plans, handoffs and chat notes.

## Cleanup

Code is either active, compatibility-retained, historical, or scheduled for removal. Before deleting a module, check supported entrypoints, tests, migration paths and rollback consumers. Remove obsolete paths rather than carrying permanent compatibility layers without a supported caller.

## Validation

Start with the cheapest deterministic checks, then run the affected unit/integration and boundary tests. Passing source tests does not by itself prove production deployment or runtime certification.
