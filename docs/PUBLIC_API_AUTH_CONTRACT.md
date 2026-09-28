# Public API Authentication Contract

The Foundation public HTTP API currently uses one operator credential supplied as a bearer token. The derived subject fingerprint is a credential-scope identifier, not a user-account identity.

Admission limits, idempotency and cursor scopes are bounded to that operator credential until a scoped multi-principal authentication system is introduced and validated end-to-end. Public documentation must not describe these limits as per-user quotas.

Bearer scheme parsing is case-insensitive and surrounding token whitespace is ignored. Missing or malformed credentials fail closed.

Unexpected request-body/runtime exceptions must not be reclassified as malformed input merely because JSON parsing occurs. Only input, decoding and schema errors belong to the malformed-input class.

The authentication model is intentionally simple and single-operator. Any future move to per-client/per-user credentials must update this contract, its acceptance tests, and the public/private boundary documentation together.
