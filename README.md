# Workspace Foundation

General-purpose application components for structured web data processing, provenance-aware records, deterministic workflows, and bounded external integrations.

## Status

Pre-production foundation. The repository is intentionally limited to publishable application primitives and public-safe interfaces.

## Scope

- Data contracts and request models
- Deterministic planning and processing utilities
- Source and provenance primitives
- Evidence and relationship data structures
- Provider and acquisition interfaces
- Bounded public HTTP/Worker execution
- Public-safe tests and build checks

Protected operational authority, private evaluation material, deployment authorization, credentials, and other non-public controls are maintained separately.

## Design principles

- Deterministic logic before model-assisted logic
- Explicit provenance for externally derived data
- Hard resource and cost limits
- Fail-closed behavior when required capabilities are unavailable
- No credentials committed to source control
- No automatic bypass of access controls

## Development

```bash
pytest tests/ -v
```

The project also includes Cloudflare Worker and D1/R2 deployment scaffolding. Account-specific resources and credentials are supplied only through deployment configuration and secret storage.
