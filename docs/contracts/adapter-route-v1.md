# Adapter Route Contract v1

Public-safe contract for routing bounded compute jobs to a private extractor/mapper
implementation.

## Envelope

A route consists of:

- `stage`: `extract` or `map`
- `adapter_key`: stable platform/site-family identifier
- `method`: deterministic method name from the allowed adapter registry
- `input_sha256`: hash of the immutable input artifact
- `contract_version`: route contract version
- `policy_profile`: opaque policy identifier evaluated by protected operations

## Rules

The public control plane must not carry credentials, cookies, private source URLs,
selector secrets, provider tokens, or implementation details that are not required
to route the job.

The private executor validates the route against its adapter registry and rejects
unknown adapter/method combinations.

The result returns only through the versioned execution-result contract. Large raw
responses, images, PDFs, traces, and other artifacts are stored separately and
referenced by hash/URI.

## Evolution

Adding an adapter is backward-compatible when the existing route fields remain
valid. Changing method semantics requires a new adapter or method version and a
replay/evaluation comparison before protected promotion.
