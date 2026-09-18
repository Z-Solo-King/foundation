# GitHub Actions dispatch through the public Foundation router

The canonical public entrypoint for family automation is `.github/workflows/foundation-canonical-workflow-bridge.yml`.

Private Operations and the private runtime must not dispatch target workflows directly. They use the Foundation GitHub App installation credential to invoke the public Foundation router, which validates the requested target and then dispatches the canonical Foundation workflow with its own Foundation App token.

## External/private-runtime route

The router accepts a `repository_dispatch` event with:

- `event_type`: `foundation_action`
- `client_payload.target`: one of the allowlisted Foundation workflows;
- `client_payload.dry_run`: only for nightly research;
- `client_payload.confirm_production`: mandatory for production release;
- `client_payload.operations_ref`: optional branch or immutable SHA for centralized Operations validation.

The GitHub App used for this external route must be installed on `Z-Solo-King/foundation` and have the repository permission needed to create `repository_dispatch` events (Contents: write). GitHub documents that GitHub App installation tokens can create repository dispatch events and that the workflow-dispatch endpoint uses Actions: write. citeturn780788search0turn780788search4

## Allowlisted Foundation targets

The router currently permits only:

- `.github/workflows/nightly-multi-agent-research.yml`
- `.github/workflows/heroic-ai-production-release.yml`
- `.github/workflows/cross-repository-contract-drift.yml`
- `.github/workflows/operations-centralized-validation.yml`
- `.github/workflows/main-push-actions-control-plane-probe.yml`

No private Operations workflow is introduced.

## Nightly research

The canonical nightly research workflow is `.github/workflows/nightly-multi-agent-research.yml`. It pins the approved Operations revision and verifies the exact commit before checkout.

`dry_run=true` is permitted only for explicit manual testing. Live research remains subject to its own preflight and evidence gates.

## Production

The production release workflow remains protected behind explicit `confirm_production=true`. The router never bypasses the production workflow's own guards.

## Boundary

Foundation remains the sole GitHub Actions execution/dispatch owner. Operations remains the private source/runtime/policy authority. This routing contract adds an external ingress to the existing public bridge; it does not create a second CI/CD owner or deployment path.
