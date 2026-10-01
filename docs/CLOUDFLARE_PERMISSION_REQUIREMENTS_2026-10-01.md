# Cloudflare permission requirements — 2026-10-01

## Connector state

The Cloudflare connector currently fails authenticated requests with Invalid API Token.

Therefore the connector can inspect Cloudflare API schemas and documentation, but it cannot currently read or mutate this account's private Worker/D1/R2/Queue/Billing resources.

## Required API permissions

Use a dedicated Cloudflare API token rather than a global API key.

| Capability | Minimum permission |
|---|---|
| Verify token | valid token |
| Read Workers metadata | Workers product Metadata Read-Only (or legacy Workers Scripts Read where applicable) |
| Read/update/deploy existing Workers | Workers product Editor |
| Create/delete Workers | Workers product Admin |
| Read D1 | D1 Read |
| Update D1/schema | D1 Edit |
| Read R2 | Workers R2 Storage Read |
| Update R2 | Workers R2 Storage Edit |
| Read Queues | Queues Read |
| Publish/modify Queues | Queues Edit |
| Read Workers AI/model/account state | Workers AI Read |
| Run/update Workers AI through REST | Workers AI Edit |
| Read billable usage | Billing Read |
| Billing mutations | do not grant unless explicitly required |
| Change Worker Routes/Custom Domains | Worker Editor plus zone Workers Routes Write |

Browser Run Quick Actions and CDP require Browser Rendering - Edit through the REST API. Browser Run can also be used through a Worker binding without an API token for the bound call.

## Scope recommendation

Scope the token to the single project account. Where resource-level scope is supported, prefer the individual Worker, bucket, database or other resource instead of account-wide write access.

Do not use Read All Resources or a global API key merely to make the connector work.

## How to repair the connector credential

1. Cloudflare Dashboard -> My Profile -> API Tokens.
2. Create a Custom Token.
3. Add the minimum account permissions above.
4. Restrict account/resource scope to this project.
5. Optionally restrict client IPs and token TTL.
6. Copy the token once; Cloudflare only displays the secret when created.
7. Replace the connected Cloudflare credential used by this project/tool with the new token.

Then run Foundation workflow cloudflare-permission-readiness.yml.

The workflow performs only read requests. It never creates/deletes resources, changes billing, deploys Workers, or consumes Browser Run quota.

## Browser Run note

A safe permission probe cannot use the Browser Run screenshot/content/scrape/crawl/json POST endpoints because those execute Browser Run and can consume quota.
The required REST permission is Browser Rendering - Edit.
The project should continue to prefer Worker bindings, paced fallbacks, strict zero-cost admission, and no challenge bypass or clearance-cookie replay.

## GitHub Actions secret boundary

The repository expects CLOUDFLARE_API_TOKEN and CLOUDFLARE_ACCOUNT_ID as protected workflow inputs.
The current GitHub connector can manage repository code, issues and pull requests, but it does not expose a repository-secret write operation in this session.
GitHub's REST API supports repository secrets; fine-grained tokens need repository Secrets: write permission.
Therefore the credential replacement must be done through GitHub Settings/Secrets or an authorized GitHub API/CLI path outside this connector.

## Safety

Never put Cloudflare API tokens in source files, workflow YAML, issue/PR text, backup artifacts, logs or public manifests.
Cloudflare recommends granular API tokens and limiting token use by IP and/or TTL where practical.
