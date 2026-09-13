# Cloudflare verification continuity — September 14, 2026

Cloudflare production verification for this project is intentionally performed through the established chatbot/control-plane bridge rather than from arbitrary local network execution environments.

Authoritative verification chain:

1. `deploy-public-worker.yml` authenticates to Cloudflare, discovers the `research-intelligence` D1 database, applies remote migrations, and deploys the public Worker. It runs on `main` pushes/manual dispatch and waits for the same commit's `public-tests` workflow to complete successfully before touching Cloudflare.
2. `production-chatbot-deploy-smoke.yml` runs on `main` pushes/manual dispatch, waits for the same commit's deployment workflow to succeed, verifies public Worker `/health`, and then calls the authenticated chatbot diagnostic operation `infrastructure_verify_public_test`.
3. The chatbot diagnostic is authoritative for protected checks including public chatbot reachability, Cloudflare D1, and Backblaze B2 lifecycle checks.

This is deliberate: local environments may not resolve the public Worker hostname even when production is healthy. A failed local DNS/network probe is therefore not interpreted as a Cloudflare production failure.
