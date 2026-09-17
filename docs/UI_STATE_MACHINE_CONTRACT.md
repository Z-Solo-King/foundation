# UI / Backend State-Machine Contract

**Status:** Canonical public UI acceptance contract
**Owner:** Foundation frontend/public boundary; backend result states remain authoritative.

The browser may render a lifecycle state only from an explicit backend or local transition. Missing fields are `UNKNOWN`, never success.

| Lifecycle | Required semantic state |
|---|---|
| New chat | `NEW_CHAT` |
| Submit | `SUBMITTING` |
| Accepted | `QUEUED` |
| Execution | `RUNNING` |
| Model stream | `STREAMING` |
| Success | `COMPLETE` |
| Retained work with incomplete work | `PARTIAL` |
| Policy/auth denial | `BLOCKED` or `REJECTED` |
| Dependency unavailable | `UNAVAILABLE` |
| Missing execution evidence | `UNKNOWN` / `NOT_ATTEMPTED` |
| Connection loss | `RECONNECTING` |
| Durable continuation | `RESUMED` / `REPLAYED` |
| Expired session | `AUTH_EXPIRED` |

Duplicate submissions must remain distinguishable from retries. Replayed events must not manufacture a second completion. Research requires an active chat before submission. Provider names, policy internals, credentials and protected diagnostics are never UI state.

Acceptance tests validate lifecycle semantics and backend authority rather than DOM presence alone.
