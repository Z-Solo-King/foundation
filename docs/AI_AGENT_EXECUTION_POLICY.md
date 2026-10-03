## 9. Acquisition source selection
Acquisition is capability-driven, not tied to one transport. Browser retrieval, direct HTTP/HTML, public APIs, feeds, structured page data and search discovery may all be used when available and appropriate to the requested data. A transport failure is a signal to select another available acquisition mode or record \`unresolved_transport\`; it is not by itself a data-negative result. Preserve source provenance and acquisition mode in evidence.

**Policy lock:** never add a project-wide rule that disables browser/API/feed/HTTP acquisition as a class. Route by requested data, source capability, runtime state, cost/resource budget, and evidence requirements.

## 10. Audit routing
\`docs/AI_AUDIT_SYSTEM.md\` is the routing guide; \`docs/AI_PROJECT_MAP.json\` is navigation metadata. Contracts, owner registries, source, tests and runtime receipts remain authoritative.
Large audits begin issue/context-first and use map-first retrieval, adaptive lanes, root-cause clustering and second-lens validation. Compute-inspired patterns are optional engineering analogies.

## 11. Migration / polyglot
Language changes are evidence-driven. Python remains protected semantic/policy/provenance/replay/resource authority until formal promotion. Candidates need contract, differential, adversarial, performance/resource, shadow, canary and rollback evidence.

## 12. Completion
Remaining work must be explicit \`RUNTIME\`, \`EXTERNAL/ADMIN\`, \`DUPLICATE/SUPERSEDED\` or \`ROADMAP\`, with canonical owner and missing evidence recorded.


## 13. Workflow authority routing

Before editing code or selecting an Action, identify the workflow authority class for the task.

Public feed discovery routes through Foundation public-safe workflows. Do not redirect public feed discovery to private Operations Actions.

Privileged workflows that access secrets or private Operations are main/schedule/manual execution surfaces only. They must not execute on pull_request, pull_request_target, or merge_group.

The workflow authority registry is the machine-checkable source for this boundary. If validation fails, stop at routing/acceptance before implementation.

## 14. Security protocol and privileged automation
Security controls are part of the execution contract.

- `workflow_run` and other privileged triggers must operate only on trusted source. Never check out or execute untrusted pull-request or fork code in a workflow that can access secrets or write-capable tokens. Use least-privilege `GITHUB_TOKEN` permissions and read-only GitHub App installations wherever possible.
- AI agents and AI-generated benchmark/research output are advisory evidence. They must never gain merge, deploy, policy, provider-promotion or production-authority powers through automation.
- Cloudflare production Workers, bindings, secrets and immutable deployment pins are production-owned state. Normal changes flow through the canonical Foundation release workflow on protected `main`; direct connector mutation is not a normal deployment mechanism.
- Private runtime inspection must be separated from public evidence. Raw private API responses, credentials, provider responses and private revision identifiers must never be uploaded to public artifacts or posted to public issues. Sanitize receipts and delete raw inspection data before publication.
- Production pin checks are lineage checks: an approved revision may legitimately remain an ancestor of a moving `main`. Do not interpret ordinary forward advancement as integrity drift.
- Required security, hygiene, provenance and release gates are fail-closed. Never weaken or bypass them merely to obtain a green status. External credential/token-health failures remain explicitly classified as `EXTERNAL/ADMIN`.
- Use parallel lanes for independent investigation only; serialize writes, production changes and merges.
