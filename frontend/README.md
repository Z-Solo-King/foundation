# Frontend

The frontend keeps browser-local chat/project/saved state in `app.js`. `lifecycle_controller.js` is the canonical owner of Research-mode transport, polling, reconnect/recovery, durable research queueing, active-run state, and idempotency.

`app.js` must remain a UI/bootstrap boundary and must not become a second Research lifecycle authority. During the migration, the lifecycle controller intercepts Research-mode interactions at the capture boundary so there is one runtime transport/queue/active-run owner.

`lifecycle_queue_controls.js` owns the canonical research queue UI. `session_bridge.js` owns the browser session bridge. No frontend module should introduce a second research transport, queue, or active-run persistence authority.
