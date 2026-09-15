# Frontend

The frontend keeps browser-local chat/project/saved state in `app.js`, while `lifecycle_controller.js` is the canonical owner of Research-mode transport, polling, reconnect/recovery, durable research queueing, active-run state, and idempotency.

`app.js` remains responsible for general UI bootstrap/rendering and local chat organization. It must not become a second Research lifecycle authority. Research-mode interactions are intercepted by `lifecycle_controller.js` at the capture boundary and use its durable queue/active-run contract.

`lifecycle_queue_controls.js` owns the queue UI for the canonical lifecycle. `session_bridge.js` owns the browser session bridge. No frontend module should introduce a second research transport, queue, or active-run persistence authority.
