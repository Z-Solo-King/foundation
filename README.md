# Research Intelligence Engine — Public Core

Public, publishable implementation of a zero-dollar personal research intelligence engine.

This repository intentionally contains only public-safe application contracts, deterministic research/evidence primitives, generic provider interfaces, and public-safe tests. Protected policy authority, private evaluation holdouts, promotion authority, deployment secrets/configuration, and private operational state belong in the private control plane.

## Current Status

The repository contains a substantial research/evidence prototype, but it is **not yet a production-ready deployment**. Production integration, private control-plane integration, real Cloudflare persistence/runtime wiring, real acquisition integrations, and final adversarial verification remain required.

## Architecture

```text
Client/UI
   ↓
HTTP API
   ↓
Planner
   ↓
Acquisition
   ↓
Observations
   ↓
Evidence verification
   ↓
Synthesis
   ↓
User-facing result

Protected decisions ──→ Private control plane
```

### Public / Private Boundary

PUBLIC:
- Research request/plan contracts
- Deterministic evidence and provenance structures
- Generic acquisition/provider interfaces
- Public worker protocol and validation primitives
- Public-safe tests and documentation

PRIVATE:
- Protected policy authority
- Production promotion/canary/rollback authority
- Private benchmark holdouts and expected results
- Deployment configuration and operational trust decisions
- Private evidence/state authority and protected security policy

The public repository must never be treated as the authority for protected policy or production promotion.

## Evidence Model

Canonical provenance path:

```text
Claim → EvidenceSpan → DocumentVersion → Source → SourceFamily → SourceLineage
```

Evidence certificates provide integrity/structural verification for evidence spans; they do not substitute for epistemic truth.

Claim states include SUPPORTED, CORROBORATED, CONTRADICTED, UNKNOWN, INACCESSIBLE, STALE, PARTIAL, and INFERRED.

## Runtime Constraint

Target: **$0/month runtime**.

All external provider usage must pass explicit free-eligibility and no-overage gates. Development-time coding assistants are optional and are never runtime dependencies.

## Development

Run the public test suite with:

```bash
pytest tests/ -v
```

Before merging public changes:

1. Keep one canonical implementation per behavior.
2. Do not add private authority or secrets.
3. Preserve evidence provenance and explicit claim states.
4. Preserve hard resource and no-overage constraints.
5. Keep public workers untrusted and fail-closed.
6. Run the full public test suite.

## Private Control Plane

The companion private repository is:

`Z-Solo-King/research-intelligence-engine-private`

It contains protected policy, promotion authority, private evaluation assets, deployment contracts, and security-sensitive tests.

## Status Discipline

Passing public unit tests does **not** prove overall production readiness. Production readiness requires the public repository, private control plane, Cloudflare runtime integration, real acquisition paths, security controls, and private holdout evaluation to pass their respective gates.
