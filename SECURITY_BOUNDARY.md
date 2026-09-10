# Public Security Boundary

This repository is intentionally limited to publishable implementation primitives.

## Must not be added here

- Secrets, credentials, private data or private evidence
- Private evaluation answers/holdouts
- Production promotion/canary/rollback authority
- Protected policy authority
- Deployment authorization logic
- Trust decisions that require private state

## Required pattern

Public code may emit proposals, metrics, or validation facts. Protected decisions are made by the private control plane.

## Production status

This repository is a public-safe core, not a standalone production deployment. Production readiness requires the private control plane and real runtime integration to pass their respective gates.
