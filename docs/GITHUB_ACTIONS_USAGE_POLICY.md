# GitHub Actions Usage Policy

## Private Operations repository: restricted until October 2026

The private `Z-Solo-King/operations` repository is **not an available GitHub-hosted execution environment during the September 2026 quota period**.

### Mandatory rule

Until the private Actions quota becomes available again in **October 2026**, do not design, trigger, or depend on any workflow that executes runtime work inside `operations`.

This restriction includes:

- GitHub Actions workflows stored in `operations`;
- GitHub-hosted benchmark runners that require an `operations` checkout;
- private-repository CI as a prerequisite for public benchmark/test completion;
- long-running chatbot/background jobs whose execution depends on private Actions minutes;
- treating the private repository as if it has unlimited GitHub Actions capacity.

### Current execution owner

For automated GitHub-hosted testing, `Z-Solo-King/foundation` is the execution owner until this restriction is lifted.

Public workflows must:

- run on GitHub-hosted runners from `foundation`;
- use only code and test fixtures that are safe to execute from the public repository;
- keep credentials and protected production configuration out of source and artifacts;
- persist only sanitized benchmark summaries/results;
- fail truthfully when a required capability is unavailable.

### October is not "unlimited"

When private GitHub Actions access becomes available again in October 2026, it must **not** be treated as unlimited capacity. Before moving workloads back to `operations`, verify the actual current quota/allowance and keep public `foundation` as the preferred execution location for workloads that are safe to run publicly.

Any move of execution back into `operations` requires an explicit capacity check and architecture decision; do not assume that the quota reset permits unrestricted long-running workloads.

### Boundary with Cloudflare

This policy concerns GitHub repository execution only. It does not authorize changes to Cloudflare configuration, Workers Builds, Deploy Hooks, production D1, or Worker secrets.

_Last updated: 2026-09-14._
