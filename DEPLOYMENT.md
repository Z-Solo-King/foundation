# Deployment

This repository is the public-safe Worker component. The protected control plane is deployed separately from the private repository and is reached through the `CONTROL_PLANE` service binding.

## Required Cloudflare resources

Create a D1 database named `research-intelligence` and an R2 bucket named `research-intelligence-artifacts`. Put the resulting D1 database ID into `wrangler.toml`.

Do not put API tokens or authentication secrets into Git. The public Worker expects an `AUTH_TOKEN` secret in production.

## Migration

Apply the checked-in SQL migrations to the D1 database before first production use.

## Python Worker

Cloudflare currently supports Python Workers with the `python_workers` compatibility flag and bindings such as D1, R2 and Service Bindings. Deploy with Pywrangler/Wrangler using the checked-in `pyproject.toml` and `wrangler.toml`.

## Private control plane

Deploy `research-intelligence-engine-private` as the service named `research-intelligence-engine-private`. Do not expose a public route for the private Worker.

## Production gate

Deployment is not considered complete until `/readiness` reports the private control plane as ready and a real research request persists run/source/observation state successfully.
