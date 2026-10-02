# Migration Continuation — Public-Safe Pointer

This file is the public-safe continuation pointer for the Heroic AI GitHub + Cloudflare migration.

## Repository boundary

- **Foundation** (`Z-Solo-King/foundation`) is the public contract, edge, hosted CI, and release boundary.
- **Operations** (`Z-Solo-King/operations`) is the private runtime and operational authority.
- Private infrastructure identifiers, deployment/version identifiers, credentials, secret names, provider inventories, immutable private-repository pins, and live operational receipts are intentionally not recorded in this public repository.

## Current-state authority

Do not use this dated handoff as a live-state source of truth. Current state must be derived from:

1. the current `main` branches;
2. the repository's canonical architecture/ownership documents;
3. live GitHub Actions evidence;
4. live Cloudflare state when operational verification is required.

## Migration rule

A responsibility must have one canonical implementation owner. Compatibility layers may expose public contracts, but must not duplicate private runtime algorithms.

## Security rule

This public repository must not contain operational credentials or private infrastructure topology. Historical exposure is handled separately from the current-tree migration and security controls.

## Continuation

For private operational details, continue from the canonical Operations repository and its current documentation. This file exists only to prevent future chats from treating a stale public handoff as authoritative.

_Last reviewed: 2026-10-02._