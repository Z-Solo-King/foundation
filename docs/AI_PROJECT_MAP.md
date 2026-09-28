# AI Project Map — Foundation

**Purpose:** human-readable companion to `docs/AI_PROJECT_MAP.json`.
**Audience:** humans and AI agents performing architecture scans, issue triage, documentation cleanup, code review, benchmarks, migration and runtime reconciliation.
**Security:** secret values are never stored here. Names/classes/purpose are documented only when safe.

## 1. What this map is for
The map is a navigation layer. It answers: **what is connected to what, why it is connected, how it communicates, what authenticates it, which repository owns the behavior, which functions implement it, which policy rules govern it, and what evidence is required.**

Use the map before reading large code surfaces. Resolve the feature/function/policy path first, then retrieve only the source needed for the current uncertainty.

## 2. System at a glance

```text
Browser / Product UI
    ↓
Foundation public application
    ↓ HTTPS / public boundary
Cloudflare Worker: heroic
    ├─ ASSETS
    ├─ D1: research-intelligence
    ├─ Backblaze B2
    └─ service binding: OPERATIONS
             ↓
       operations-edge
             ↓ CORE service binding
        operations control plane
             ├─ Workers AI
             ├─ D1: research-intelligence
             ├─ chatbot routing/providers
             ├─ resource governance
             ├─ research orchestration
             └─ promotion/evaluation
```

Foundation remains the public contract/deterministic-core owner. Operations remains the protected control-plane owner.

## 3. Connection matrix

| ID | From → To | Mechanism | Why | Auth | Owner | Main policies | Evidence |
|---|---|---|---|---|---|---|---|
| CONN-FND-APP-WORKER | frontend → heroic | HTTPS | user-facing ingress, chat and stream | public boundary/session semantics | Foundation | P002 P003 P006 P015 | R2; live R3/R4 |
| CONN-FND-WORKER-OPS | heroic → operations-edge → operations | service binding | private chatbot/research execution | inbound Bearer is forwarded; Operations checks CHAT_BACKEND_TOKEN, then Operations AUTH_TOKEN | Operations | P002 P003 P008 P015 | repo R1/R2; runtime R3/R4 |
| CONN-FND-WORKER-D1 | heroic → research-intelligence | D1 binding `DB` | research runs, admissions, evidence/publication | native binding | shared family data contract | P003 P004 P007 P008 | runtime binding |
| CONN-FND-WORKER-B2 | heroic → Backblaze B2 | object-storage/S3-compatible path | artifact/storage dependency and release persistence | B2 key ID + application key | Foundation | P002 P006 P007 P015 | source/release; B2 receipt for object claims |
| CONN-FND-GITHUB-ACTIONS-RELEASE | GitHub Actions → Cloudflare/B2/GitHub | Actions | canonical build/release/acceptance orchestration | `github.token` + scoped repo/environment credentials | Foundation | P009 P012 P015 | workflow/release receipt |
| CONN-FND-GITHUB-OPS-APP | Foundation Actions → Operations repo | GitHub App installation token | read/validate pinned private revision | Operations App credentials → short-lived installation token | Foundation bridge / Operations boundary | P002 P009 P015 | workflow receipt |
| CONN-FND-OPS-RETURN | operations → heroic | service binding `FOUNDATION` | consume public-safe Foundation contract/core | Operations AUTH_TOKEN carried in protected request | Operations | P001 P002 P003 P015 | runtime receipt |

## 4. Credential and token map

| Credential | Where | Purpose | Important rule |
|---|---|---|---|
| `github.token` | Foundation GitHub Actions | GitHub API/workflow operations | automatic per-workflow token; not a persistent repository secret |
| `OPERATIONS_APP_ID` + `OPERATIONS_APP_PRIVATE_KEY` | Foundation GitHub Actions secrets | create short-lived GitHub App installation token for private Operations access | never publish values; App token is the runtime access credential |
| `AUTH_TOKEN` | Foundation/Heroic Cloudflare Worker secret | Foundation-side authentication | separate value from Operations `AUTH_TOKEN` |
| `B2_KEY_ID` + `B2_APPLICATION_KEY` | Foundation release + Heroic Worker | Backblaze B2 authentication | separate from GitHub tokens and Cloudflare API token |
| `CLOUDFLARE_API_TOKEN` + account ID | Foundation release environment | deploy/verify Cloudflare | deployment credential, not app-user authentication |
| Operations secrets | private Operations control plane | protected runtime authentication | never copy into public Foundation |

### Credential identity rule
`credential identity = surface + repository/Worker + environment + purpose`.

Therefore:
- `Foundation AUTH_TOKEN` ≠ `Heroic AUTH_TOKEN` ≠ `Operations AUTH_TOKEN`, even when names are identical.
- `OPERATIONS_APP_PRIVATE_KEY` ≠ the short-lived GitHub App installation token.
- `github.token` ≠ any repository secret.
- B2 credentials ≠ Cloudflare API credentials.

## 5. Foundation application flow

1. `frontend/index.html` and `frontend/app.js` provide the user-facing application.
2. Public request enters `worker.py`.
3. Request/auth/admission/idempotency boundaries run before protected execution.
4. The Worker delegates private chat/research work through the `OPERATIONS` service binding.
5. Operations returns a private result.
6. Foundation converts it into the public-safe JSON/SSE response and publication/evidence boundary.

Key public functions include `_authorized`, `_public_admit`, `_operations_chat`, `_operations_chat_stream`, `_publish_evidence`, `_idempotency_key` and `fetch`.

## 6. Cloudflare topology

The current live family topology observed on 2026-09-28 is:

| Worker | Role | Important bindings |
|---|---|---|
| `heroic` | canonical source-controlled Foundation public Worker | ASSETS, DB, B2_*, AUTH_TOKEN, OPERATIONS → operations-edge |
| `operations-edge` | thin delegation edge | CORE → operations |
| `operations` | private control plane | AI, OPERATIONS_DB, FOUNDATION → heroic, protected secrets/policy vars |
| `foundation` | separate live Worker observed in account | purpose/ownership not established by this map |

The service graph is therefore topology-cyclic (`heroic → operations-edge → operations → heroic`). The audit rule is **not** “cycles are forbidden”; it is “each request path must remain bounded and must not recurse across the service boundary without an explicit terminal condition.”

## 7. Data layer

Cloudflare D1 database: `research-intelligence`.

Current live schema contains 22 tables/views, including:
`chat_idempotency`, `chat_learning_observations`, `chat_memory_records`, `claims`, `claim_evidence`, `evidence_spans`, `observations`, `research_runs`, `research_publications`, `resource_governance_quota`, `resource_governance_reservations`, `source_lineage`, `sources`, `feed_probe_results`, `document_versions`, and migration/legacy tables.

The Foundation binding name is `DB`; Operations uses `OPERATIONS_DB` for the same logical database. The binding name changes; the underlying data resource is shared.

## 8. Backblaze B2

Backblaze B2 is **object storage**, not Cloudflare R2.

Foundation's Cloudflare Worker exposes B2 configuration through `B2_BUCKET` and `B2_ENDPOINT` plus secret `B2_KEY_ID` and `B2_APPLICATION_KEY`. The production release script validates those credentials/configuration and checks a B2 lifecycle result before release acceptance.

Backblaze recommends the S3-Compatible API for broad SDK/tool compatibility and supports scoped application keys restricted by bucket, access type and optional file-prefix constraints.

## 9. GitHub Actions

Foundation owns the family GitHub Actions surface. Operations intentionally has no `.github/workflows/` runtime automation surface.

Important workflow responsibilities:
- public PR validation and security checks;
- canonical production release;
- private Operations access through the GitHub App bridge;
- nightly research dispatch and pinned Operations revision;
- benchmark/audit orchestration;
- sanitized receipts and issue updates.

Actions should use least-privilege permissions and immutable Action SHAs. The workflow bridge is an execution handoff, not a second application runtime.

## 10. Language map

| Language | Current surface | Why used | How AI should audit it |
|---|---|---|---|
| Python | 332 files | canonical public semantics/deterministic core | reference behavior, policy/contract analysis, tests |
| TypeScript | 18 files | typed contract/edge/tooling candidates | shadow/differential against canonical behavior |
| JavaScript/MJS | 30 files | browser/client/runtime-native logic | lifecycle, cancellation, boundary behavior |
| SQL | 10 files | D1 schema and data contract | migration order, constraints, idempotency, query bounds |
| YAML | 46 files | GitHub Actions declarative control plane | triggers, permissions, refs, secret flow, artifacts |
| Shell | 4 files | release/deployment glue | bounded commands, secret handling, failure semantics |
| JSON/TOML/HTML/CSS | configuration/data/UI surfaces | machine-readable contracts and product presentation | schema/config consistency and ownership |

Language does not determine authority. Authority comes from the family ownership map and policy.

## 11. Feature/function/policy relationship

For every feature, AI should be able to traverse:

`feature → files → functions → consumers → policy rules → tests → workflow → evidence → issue/PR`.

Examples:
- Public worker → auth/admission/idempotency → P002/P003/P008/P015 → boundary tests → live endpoint receipt.
- Research execution → run lifecycle/terminalization → P004/P007/P008 → evidence tests → runtime receipt.
- Identity mapping → normalization/routing → P001/P005/P006/P007 → differential tests.
- Release workflow → immutable refs/permissions → P009/P012/P015 → CI receipt → production receipt.

## 12. Runtime verification finding

`EVIDENCE_PACKAGE_SIGNING_SECRET` is referenced by `worker.py` during evidence publication, but the 2026-09-28 live Cloudflare binding inventory did not show that secret on the observed Foundation/Heroic Worker settings.

Status: **VERIFY_RUNTIME**.

Do not infer the value, publish it, or modify credentials from this document. Dedicated Cloudflare verification is required.

## 13. AI-fast scan procedure

1. Read `AI_PROJECT_MAP.json` + this file.
2. Resolve repository, feature and canonical owner.
3. Traverse the smallest function/file set for the question.
4. Read the mapped policy rules before judging behavior.
5. Cross-fire with a second lens: another language, tests, workflow, runtime receipt or external documentation.
6. Cluster the result under an existing issue when owner/file-surface/acceptance match.
7. Mutate only the canonical owner.
8. Re-run the narrowest evidence check.

This turns a full-project scan from repeated discovery into targeted graph traversal.

## 14. Freshness rule
Static map fields are structural snapshots. GitHub main/PR/CI state is live GitHub evidence. Cloudflare deployment/binding state is live Cloudflare evidence. Never convert a stale map row into a current production claim without refreshing it.

## External research basis
Cloudflare Workers bindings allow Workers to interact with platform resources; Cloudflare distinguishes unencrypted vars from encrypted secrets. GitHub Apps use scoped, short-lived installation tokens; GitHub Actions exposes a job-scoped `GITHUB_TOKEN`; Backblaze B2 supports S3-Compatible access and scoped application keys. Python, TypeScript, Rust and Go documentation inform the language-role rationale.

References:
- https://developers.cloudflare.com/workers/runtime-apis/bindings/
- https://developers.cloudflare.com/workers/configuration/environment-variables/
- https://developers.cloudflare.com/workers/wrangler/configuration/
- https://docs.github.com/en/apps/creating-github-apps/authenticating-with-github-app/about-authentication-with-a-github-app
- https://docs.github.com/en/rest/apps/apps
- https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/github-credential-types
- https://www.backblaze.com/docs/cloud-storage-getting-started
- https://www.backblaze.com/docs/cloud-storage-s3-compatible-app-keys
- https://docs.python.org/3.14/reference/
- https://www.typescriptlang.org/docs/
- https://doc.rust-lang.org/book/
- https://go.dev/doc/
## Compute-inspired AI patterns

The map uses ten reusable patterns. These are engineering abstractions inspired by CPU/GPU scheduling, portability and low-latency systems; they are not hardware implementation requirements.

| Pattern | Project use | Audit trigger |
|---|---|---|
| P01 Work Director | choose the next lane/task from telemetry, dependencies, evidence tier and cost | too much static ticket ordering or idle/blocked lanes |
| P02 Cross-Fire Mesh | independently validate the same contract from different boundaries | high-risk deterministic finding |
| P03 Sparse Context Access | retrieve graph-indexed slices instead of whole repositories/logs | token/time pressure or repeated rediscovery |
| P04 Capability Negotiation | choose provider/tool/language by capability + policy | portability/migration/provider fallback |
| P05 Latency Guard | measure queue/retrieval/planning/provider/persistence phases | chatbot/audit slowdown |
| P06 Shared Evidence Fabric | share artifact/receipt references without sharing private authority | cross-repo synchronization |
| P07 Compatibility Profiles | contain version/site/provider quirks in bounded profiles | recurring external incompatibility |
| P08 Blind Differential | compare normalized outputs before revealing implementation identity | benchmark or migration comparison |
| P09 Fallback Ladder | preferred -> alternate -> degraded -> blocked | provider/extraction recovery |
| P10 Shim/Sidecar | add observability/compatibility without creating a second authority | edge wrappers/adapters |

The detailed specification is in `docs/AI_COMPUTE_INSPIRED_PATTERNS.md`.

## AI Work Director
Represent work as `task_id + owner + feature + mutation_surface + dependencies + expected_cost + deadline + evidence_tier + lane_role + retrieval_budget + state + priority`.
Schedule by readiness and information gain, not ticket age alone. Blocked lanes work-steal. Shared mutation surfaces stay serialized.

## Credential identity
For any secret/token connection, identity is `surface + repository/Worker + environment + purpose`. Identical names such as `AUTH_TOKEN` do not imply identical credentials.

## Language audit rule
Each language is an independent analytical lens. Candidate implementations inherit canonical contracts and must pass differential, adversarial, performance/resource and promotion gates before authority changes.

## Token-efficiency rule
Map-first retrieval is mandatory for large audits: map -> owner -> feature -> functions -> policies -> tests/evidence -> issue/PR -> runtime receipt. Measure retrieved bytes and duplicated context.