# Chatbot UI static assets fix

**Status:** historical — fix applied; retained for incident record

The public Worker had a complete `frontend/` application but the production-generated Wrangler configuration did not declare a Workers Static Assets collection. As a result, the Worker handled `/` and returned its JSON `not found` fallback instead of serving `frontend/index.html`.

The fix configures `frontend/` as the Workers Static Assets directory and applies the same configuration to the runner-generated production Wrangler config while preserving the existing single production deployment authority. The production smoke test now also checks the HTML entrypoint and representative frontend assets.
