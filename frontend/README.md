# Frontend

The frontend keeps browser-local chat/project/saved state in `app.js`. `lifecycle_controller.js` is the canonical owner of Research-mode transport, polling, reconnect/recovery, durable research queueing, active-run state, and idempotency.

`app.js` remains the general UI/bootstrap boundary. Research-mode interactions are intercepted by the canonical lifecycle controller, and the durable queue/active-run keys belong to that controller. `lifecycle_queue_controls.js` owns only the queue presentation controls. `session_bridge.js` owns the browser session bridge.

Until the full `app.js` decomposition is completed, compatibility with the existing UI remains explicit: no second Research transport, queue, or active-run persistence authority may be introduced.
