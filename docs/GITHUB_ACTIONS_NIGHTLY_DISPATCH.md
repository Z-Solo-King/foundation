# GitHub Actions nightly research dispatch

The canonical nightly research workflow is `.github/workflows/nightly-multi-agent-research.yml`.

Its source contract intentionally retains `artifact-metadata: write`; that permission is valid GitHub Actions syntax and must not be removed as a workaround for a missing manual-dispatch control-plane surface.

The workflow pins a private Operations revision and verifies the exact commit before checkout. A separate manual dispatch bridge exists at `.github/workflows/nightly-research-dispatch-bridge.yml` so an authorized operator can trigger the canonical workflow when the native `Run workflow` control is unavailable in the GitHub UI.

The bridge dispatches the canonical workflow on `main`, passes the `dry_run` input, and waits for GitHub Actions to admit the resulting `workflow_dispatch` run. It does not change the target workflow or bypass its execution guards.
