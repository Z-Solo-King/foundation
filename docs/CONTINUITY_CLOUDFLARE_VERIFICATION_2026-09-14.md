# Cloudflare verification continuity — September 14, 2026

Cloudflare production verification for this project is intentionally performed through the established authenticated chatbot/control-plane bridge rather than arbitrary local network execution.

The authoritative diagnostic operation is `infrastructure_verify_public_test` at the public chatbot diagnostic endpoint. A successful production proof must report `public_chatbot`, `cloudflare_d1`, and `backblaze_b2_lifecycle` as passing.

A PR workflow test was executed successfully at the workflow level but did not receive `AUTH_TOKEN`; pull-request secret scope therefore cannot be used as production proof. The production proof is consequently executed from a `main` push, where the repository's configured Actions secret scope applies, and its sanitized result is written to `docs/LIVE_CLOUDFLARE_VERIFICATION.md`.

Local DNS/network failures are not interpreted as Cloudflare production failures.