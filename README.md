# Research Intelligence Engine — Public Core

Public-safe implementation of a zero-dollar personal research intelligence engine.

## Status

Substantial research/evidence prototype. **Not yet production-ready.** Production readiness requires the private control plane, real Cloudflare runtime/persistence wiring, real permitted acquisition/provider integrations, and final adversarial verification.

## Architecture

```text
Client/UI
  -> HTTP API
  -> Planner
  -> Acquisition
  -> Observations
  -> Evidence verification
  -> Synthesis
  -> User-facing result

Protected decisions -> private control plane
```

## Public / Private Boundary

Public:
- Research contracts and plans
- Deterministic evidence/provenance primitives
- Generic provider/acquisition interfaces
- Public worker validation
- Public-safe tests and documentation

Private:
- Protected policy authority
- Production promotion/canary/rollback authority
- Private benchmark holdouts and expected answers
- Deployment authorization/configuration
- Private operational state and trust decisions

The public repository must never own protected policy or final production-promotion decisions.

## Evidence

Canonical provenance:

```text
Claim -> EvidenceSpan -> DocumentVersion -> Source -> SourceFamily -> SourceLineage
```

Evidence certificates provide structural integrity checks for evidence spans; they do not establish truth by themselves.

Claim states include SUPPORTED, CORROBORATED, CONTRADICTED, UNKNOWN, INACCESSIBLE, STALE, PARTIAL, and INFERRED.

## Runtime Constraint

Target: **$0/month runtime**. Provider use must pass explicit free-eligibility and no-overage gates. Development coding assistants are optional and are never runtime dependencies.

## Development

```bash
pytest tests/ -v
```

Keep one canonical implementation per behavior, preserve evidence provenance, enforce hard resource budgets, and keep public workers untrusted and fail-closed.

## Cloudflare Deployment

The repository now contains a Python Worker entrypoint, Wrangler configuration, and initial D1 migration. Replace deployment placeholders with resources created in the owner's Cloudflare account before deployment; credentials are not committed here.

## Private Control Plane

`Z-Solo-King/research-intelligence-engine-private` owns protected policy, promotion, private evaluation, trust-boundary, and deployment contracts.
