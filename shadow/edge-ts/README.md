# TypeScript edge shadow

This is a non-production shadow implementation of the public Worker contract.

Phase A covers only:
- GET /health
- GET /readiness
- bounded JSON error handling

It deliberately does not own production deployment, routing, authentication, chat, research, or private Operations access.

Promotion requires contract fixtures and benchmark equivalence against the canonical Python Worker.
