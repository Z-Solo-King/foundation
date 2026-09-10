# Heavy-compute interchange contract v1

This is a public-safe interface between the Cloudflare control plane and bounded heavy-compute workers.

## Envelope

Required fields:

- `contract_version`: `1`
- `job_id`: unique idempotency key for the compute job
- `run_id`: research/run identifier owned by the control plane
- `stage`: one of `extract`, `map`, `replay`, `self_check`
- `input_sha256`: SHA-256 of the input artifact/payload
- `nonce`: freshness/replay-defense token
- `attempt`: positive attempt number

## Result

Required fields:

- `contract_version`
- `job_id`
- `run_id`
- `stage`
- `status`: `ok`, `retry`, `reject`, or `error`
- `output_sha256`: SHA-256 of the output artifact

Optional fields may include compact JSON-safe output and diagnostic codes. Large evidence/artifacts must be stored in the configured artifact store rather than copied into the control-plane message.

## Trust boundary

A worker result is untrusted input until the control plane verifies:

1. schema and contract version;
2. job/run identity and idempotency;
3. nonce/freshness and replay constraints;
4. output hash and artifact availability;
5. provenance/lineage metadata;
6. expected stage ownership;
7. policy and evaluation status.

This contract carries structure, not epistemic truth. A structurally valid result still requires evidence and evaluation checks before protected state changes.

## Ownership

`foundation` owns this public-safe contract. `extractor-mapper` owns implementation. `operations` owns promotion/evaluation authority. No repository should bypass the other repository's authority boundary.
