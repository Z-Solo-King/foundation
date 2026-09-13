# Cloudflare verification continuity — September 14, 2026

Cloudflare production verification for this project is intentionally performed through the established authenticated chatbot/control-plane bridge rather than arbitrary local network execution.

The authoritative diagnostic operation is `infrastructure_verify_public_test`. A successful production proof must report `public_chatbot`, `cloudflare_d1`, and `backblaze_b2_lifecycle` as passing.

The public diagnostic endpoint is now fail-closed in production and requires the configured `AUTH_TOKEN`; unauthenticated diagnostic requests are rejected. This preserves the protected verification boundary instead of relying only on caller-side workflow behavior.

The most recent main-branch verification attempt reached the authentication guard but the GitHub Actions environment supplied an empty `AUTH_TOKEN`. That result is an authentication-context blocker, not evidence of Cloudflare, D1, B2, or network failure. Do not bypass the guard or place credentials in source/public configuration. The configured repository secret must be supplied through the protected GitHub secret mechanism before authoritative production proof can succeed.

Once authentication is available, the canonical production verification path should run after the public deployment, validate Worker health, execute the authenticated chatbot diagnostic, require all three checks to pass, and write only a sanitized proof record to `docs/LIVE_CLOUDFLARE_VERIFICATION.md`.

Local DNS/network failures are not interpreted as Cloudflare production failures.
