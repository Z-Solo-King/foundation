# GitHub Actions nightly research dispatch

The canonical nightly research workflow is `.github/workflows/nightly-multi-agent-research.yml`.

Its source contract intentionally retains `artifact-metadata: write`; that permission is valid GitHub Actions syntax and must not be removed as a workaround for a missing manual-dispatch control-plane surface.

The workflow pins a private Operations revision and verifies the exact commit before checkout. The centralized public bridge is `.github/workflows/foundation-canonical-workflow-bridge.yml`; it uses the Foundation GitHub App installation credential to dispatch only the canonical Foundation workflows on `main`.

The bridge can dispatch nightly research with the explicit `dry_run` input, or the production release only with explicit `confirm_production=true`. It does not dispatch or execute anything from the private Operations repository, and it does not bypass the target workflow's guards.
