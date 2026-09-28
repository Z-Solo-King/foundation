# Public API Authentication Contract

The Foundation public Worker currently exposes a single-operator API credential. The bearer token authenticates the caller to the public service; it is not a multi-user identity system.

Admission, idempotency, cursor and research ownership data may derive a non-secret fingerprint from the authenticated credential so records cannot contain the bearer itself. That fingerprint is not a per-user identity.

The contract remains explicit until a scoped credential system (for example per-client tokens or signed short-lived credentials) is introduced and validated end-to-end.

Bearer parsing is case-insensitive for the authentication scheme and surrounding whitespace is trimmed. Missing or malformed credentials fail closed.

Unexpected request-body/runtime exceptions are not converted into invalid-JSON responses by json_object; only input, decoding and schema errors are classified as malformed input.
