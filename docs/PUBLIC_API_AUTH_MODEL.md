# Public API authentication model

The Foundation public HTTP API currently uses one operator credential, supplied
as a bearer token through the Authorization header. The derived subject
fingerprint is therefore a credential-scope identifier, not a user-account
identity.

Admission limits, idempotency and cursor scopes are intentionally bounded to
that operator credential until a multi-principal authentication system is
introduced. The public contract must not describe these scopes as per-user
quotas.

Bearer scheme parsing is case-insensitive and surrounding token whitespace is
ignored. Authentication failures remain ordinary 401 responses; unexpected
JSON-body parser/runtime failures are not converted into generic client-error
responses.
