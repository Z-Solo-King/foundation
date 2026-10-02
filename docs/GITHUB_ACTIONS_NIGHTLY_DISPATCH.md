# GitHub Actions dispatch through the public Foundation router

The canonical public entrypoint for family automation is `.github/workflows/foundation-canonical-workflow-bridge-v3.yml`.

Private Operations and the private runtime must not dispatch target workflows directly. They use the Foundation GitHub App installation credential to invoke the public Foundation router through the GitHub Actions workflow-dispatch API. The router validates the requested target and then dispatches the canonical Foundation workflow with its own Foundation App token.

## External/private-runtime route

The route is:

`private runtime -> Foundation GitHub App installation token (Actions: write) -> workflow_dispatch on Foundation canonical router -> canonical Foundation workflow`.

The current v3 bridge accepts one input: `target`. Its allowlist is limited to the Foundation control-plane probe and the canonical nightly research workflow. It does not accept or forward `dry_run`, `confirm_production`, or `operations_ref`; those values belong to the target workflow contracts and are not bridge inputs.

For nightly research, `dry_run=true` is a Foundation-owned deterministic acceptance mode on the nightly workflow itself. The production-live launch remains the canonical production-release workflow, which supplies the exact released Foundation SHA, production release run ID, and Operations research revision.

GitHub documents that GitHub App installation tokens can create workflow-dispatch events when the app has the repository `Actions: write` permission. citeturn136297search9turn136297search1

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
