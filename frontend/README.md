# Frontend

The frontend keeps browser-local chat/project/saved state in `app.js`. `lifecycle_controller.js` is the canonical owner of Research-mode transport, polling, reconnect/recovery, durable research queueing, active-run state, and idempotency.

`app.js` remains the general UI/bootstrap boundary. Research-mode interactions are intercepted by the canonical lifecycle controller. `lifecycle_queue_controls.js` owns queue presentation controls, and `session_bridge.js` owns the browser session bridge.

This preserves the existing UI contract while preventing any new second Research transport, queue, or active-run persistence authority. Broader `app.js` decomposition remains tracked under #114.
