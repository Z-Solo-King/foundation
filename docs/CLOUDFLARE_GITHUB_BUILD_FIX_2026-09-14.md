# Cloudflare/GitHub Workers Build fix

The public `wrangler.toml` intentionally contains placeholder D1 identifiers. GitHub Actions resolves the live `research-intelligence` D1 UUID at deploy time and generates `wrangler.production.generated.toml` in the runner. The generated file is used for remote migrations and `pywrangler deploy` and is not committed.

This keeps the repository's public configuration sanitized while preventing the deployment path from attempting to deploy placeholder D1 bindings.
