# GitHub Actions dispatch through the public Foundation router

The canonical public entrypoint for family automation is `.github/workflows/foundation-canonical-workflow-bridge-v3.yml`.

Private Operations and the private runtime must not dispatch target workflows directly. They use the Foundation GitHub App installation credential to invoke the public Foundation router through the GitHub Actions workflow-dispatch API. The router validates the requested target and then dispatches the canonical Foundation workflow with its own Foundation App token.

## External/private-runtime route

The route is:

`private runtime -> Foundation GitHub App installation token (Actions: write) -> workflow_dispatch on Foundation canonical router -> canonical Foundation workflow`.

The external caller supplies the same constrained inputs as the public bridge: `target`, optional nightly `dry_run`, optional production `confirm_production`, and optional `operations_ref` for centralized Operations validation.

GitHub documents that GitHub App installation tokens can create workflow-dispatch events when the app has the repository Actions: write permission. citeturn780911search4turn480911search6

## Allowlisted Foundation targets

The autonomous router does not dispatch the production-release workflow. Production deployment is a separate manual `workflow_dispatch` boundary. The router is limited to its explicitly allowlisted evidence/maintenance workflows.

No private Operations workflow is introduced.

## Nightly research

The canonical nightly research workflow is `.github/workflows/nightly-multi-agent-research-v3.yml`. It pins the approved Operations revision and verifies the exact commit before checkout.

`dry_run=true` is permitted only for explicit manual testing. Live research remains subject to its own preflight and evidence gates.

## Production

The production release workflow is manual-only and remains protected by its existing production environment/receipt guards. The autonomous router never dispatches it.

## Boundary

Foundation remains the sole GitHub Actions execution/dispatch owner. Operations remains the private source/runtime/policy authority. This routing contract adds a single public ingress to the existing bridge; it does not create a second CI/CD owner or deployment path.
