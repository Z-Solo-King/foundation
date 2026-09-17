# Public Runner / Private Operations Boundary

Foundation and Operations intentionally use a split-repository architecture. Foundation owns the public contract, deterministic evidence rules, public GitHub Actions workflows and public artifacts. Operations remains the private control plane and execution implementation.

## Execution boundary

The canonical nightly research workflow may use a Foundation GitHub-hosted runner as an execution bridge because the private Operations repository does not use its own GitHub-hosted private runner. The bridge must:

- authenticate to the exact private `Z-Solo-King/operations` repository with a GitHub App installation credential;
- verify that the target repository is private;
- verify the requested Operations revision by immutable commit SHA;
- checkout Operations only under the runner temporary directory;
- execute the private research module without committing or copying its source into Foundation;
- remove the checkout, App credentials and askpass material with an `always()` cleanup step.

The public workflow is an execution bridge, not an ownership transfer of private implementation.

## Public artifact boundary

Private agent output crosses into the Foundation artifact surface only through versioned public-safe schemas. The canonical program artifact is `nightly-research-program/v1`; only these top-level fields are public:

- `schema`
- `program_id`
- `lane`
- `slot`
- `status`
- `measurement`
- `findings`

Measurements are aggregate execution metrics only. Findings are restricted to the claim/source/evidence fields defined by the public boundary validator. Agent prompts, notes, arbitrary nested execution context, private topology, credentials and provider response objects are not part of the public contract.

`benchmark.public_runner_boundary` provides deterministic validation of this schema, including unknown-field rejection, credential-pattern rejection, private-host rejection, lane/slot validation and duplicate-program detection. Its regression suite is deliberately adversarial.

Capacity-comparison artifacts are aggregate measurements and must not serialize nested `ProgramResult` or agent-level data.

## Evidence limits

Passing the repository validator proves only that the serialized artifact conforms to the repository-owned public schema. It does not certify private-runtime correctness, secret configuration, GitHub administration, Cloudflare production, B2 recovery, or L4 production execution. Those remain separate evidence classes.

## Ownership

Foundation must not import or reimplement protected Operations policy. Operations owns acquisition, extraction, mapping, verification, provider execution and private orchestration. Foundation owns the public artifact contract and the trust boundary at the point where private execution output becomes publicly retained repository/workflow data.
