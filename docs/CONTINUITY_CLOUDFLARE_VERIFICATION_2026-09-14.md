# Cloudflare verification continuity — September 14, 2026

Cloudflare production verification for this project is intentionally performed through the established chatbot/control-plane bridge rather than from arbitrary local network execution environments.

Authoritative verification chain:

1. `deploy-public-worker.yml` authenticates to Cloudflare, discovers the `research-intelligence` D1 database, applies remote migrations, and deploys the public Worker.
2. `production-chatbot-deploy-smoke.yml` verifies public Worker `/health` and then calls the authenticated chatbot diagnostic operation `infrastructure_verify_public_test`.
3. The chatbot diagnostic is authoritative for protected checks including public chatbot reachability, Cloudflare D1, and Backblaze B2 lifecycle checks.

This is deliberate: local environments may not resolve the public Worker hostname even when production is healthy. A failed local DNS/network probe is therefore not interpreted as a Cloudflare production failure.

The smoke workflow is also manually dispatchable so the established bridge can be exercised without depending on a new deployment event.
