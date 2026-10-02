# AI System Directory

This is the human/AI routing entrypoint for the combined Foundation + Operations architecture.

## Start here

1. Read this directory.
2. Read docs/AI_SYSTEM_MAP.json.
3. Resolve the task to a functional plane and canonical component.
4. Open the most-specific canonical path.
5. Read its governing contract/policy and tests.
6. Inspect the workflow and evidence surface.
7. Use live GitHub/Cloudflare state only for runtime claims.

The older AI_PROJECT_MAP.md/.json files remain detailed compatibility views. This directory is the navigation overlay that connects them with the improvement matrix, observability, audit, evolution, and autonomous-engineering systems.

## Where things go

| Task | Go first | Then |
|---|---|---|
| Chat / model execution | operations/private/chatbot/ | provider runtime, resource governance, run receipts |
| AI provider health/quota | operations/private/chatbot/provider_runtime.py | dashboard/provider matrix, fleet probe |
| Scraping / crawling | operations/extractor_mapper/ | acquisition planner, browser acquisition |
| Browser / JS-heavy acquisition | operations/polyglot/browser-acquisition/ | browser evolution evidence |
| WooCommerce / Merchant feed | operations/private/feed_recovery/ | Foundation public feed workflows, mapper |
| Product mapping / normalization | foundation_core/ | Operations mapper/observation contract |
| Research / evidence | backend/intelligence/ | Operations multi-agent runtime, research workflows |
| Cloudflare Worker / D1 / Workers AI | operations/private/dashboard_cloudflare_usage.py | operations/worker.py, Cloudflare bindings |
| Browser Run / AI Gateway | operations/private/dashboard_cloudflare_usage.py | operations/private/dashboard_cloudflare_ai_gateway.py |
| Quota / reservation / lease | operations/private/durable_resource_ledger.py | reconciliation + protected execution |
| B2 backup / restore / retention | .github/workflows/b2-repository-backup.yml | scripts/cleanup_b2_backup_generations.py |
| Audit / scan / drift | tools/project_observability_audit.mjs | Operations tools/master_audit.py / tools/evolution_audit.py |
| Quality telemetry | operations/private/project_observability.py | dashboard + D1 maintenance receipt |
| Evolution / candidate learning | operations/private/evolution_engine.py | private/evolution_score.py and integration bridge |
| Autonomous engineering | tools/autonomous_engineering_supervisor.mjs | deterministic mission router + allowlisted workflow |
| Migration / portability | operations/polyglot/ | Foundation migration workflows + evolution evidence |
| Current state | docs/CURRENT_SOURCE_OF_TRUTH.md | live GitHub/Cloudflare evidence |

## Category model

Do not force every feature into one bucket. The system uses orthogonal categories so the same feature can be found from multiple useful directions:

- functional plane: what the feature does;
- execution class: how it runs;
- authority layer: what it is allowed to decide;
- evidence class: how its claims are established;
- resource class: what quota/cost/limits affect it.

For example, Browser Run belongs to both Acquisition + Extraction and Runtime + Resources. A feed recovery task belongs to Acquisition + Extraction, while its payload validation and lineage also connect to Research + Evidence.

## AI direction rules

When an AI agent receives a task:

intent -> category -> owner -> canonical path -> contract -> tests -> workflow -> evidence -> runtime

Do not begin with repository-wide reading when the directory already resolves the feature.

For ambiguous tasks, choose multiple orthogonal categories rather than inventing a new category. For cross-cutting tasks such as monitor everything, start with governance_security + runtime_resources + automation_evolution, then expand only where the evidence shows a real gap.

For self-learning or self-evolving, route to the evolution/learning layer but keep the output bounded to candidate/evidence actions. Do not let the map, score or AI planner become policy or promotion authority.

## Never route here

Do not route runtime work to the retired standalone extractor-mapper repository. Do not introduce Cloudflare R2. Do not treat the dashboard or telemetry score as production-acceptance authority. Do not treat AI output as evidence without the canonical evidence chain.

## Shared AI instructions

GitHub supports repository-wide, path-specific, and agent instructions. Keep this directory as the semantic router and keep path-specific instructions focused on local constraints rather than duplicating the whole architecture.

### Autonomous governance sweep
- Contract: `docs/AUTONOMOUS_GOVERNANCE_SCAN_CONTRACT.json`
- Observation: `tools/comprehensive_governance_scan.py`
- Publication: `tools/publish_governance_findings.py`
- Scheduler: `.github/workflows/twice-daily-autonomous-governance-sweep.yml`
- AI remediation authority: `tools/autonomous_engineering_supervisor.mjs`
