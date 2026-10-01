# Hybrid & Alternative Ecosystem Audit — 2026-10-01

## Mission

**Hybrid & alternative** means a paid, premium, hosted, or proprietary product is not ignored because it costs money. It is treated as a public capability reference. We extract useful ideas, feature behavior, function structure, schemas, policy rules, resource controls, error handling, lifecycle, UX, security, and architecture, then reproduce safe portions using free/native/open-source mechanisms.

The $0 boundary applies to **runtime dependency and project spend**, not to research scope.

## Supplied corpus coverage

| Ecosystem | Supplied entries | Unique entries | Fingerprint |
|---|---:|---:|---|
| MCP | 339 | 339 | 29f7414916991321923592383f971a72ef25d06f234197b2f6d770a94e5ee4c4 |
| GitHub Actions Marketplace | 9,999 | 9,999 | 70f1fb06dbbc147050a33c8c256321eff47a1c0fce3f92b5d13a2fdf84362228 |
| GitHub Apps Marketplace | 1,408 | 1,408 | 39253b8dea75729f274e9c9af6186cc615b0a940e9d746cf7487b6213327c7e4 |

The MCP scope is the supplied `github.com/mcp?page=12` workbook sheet. It is not presented as the entire live MCP Registry. The Actions and Apps counts are the complete supplied workbooks.

## What we mine

Every candidate is inspected against the same feature vocabulary:

- interface and input/output schema;
- function decomposition and orchestration;
- tool/app/action boundaries;
- policy and permission rules;
- authentication and authorization;
- caching, batching, pagination and concurrency;
- retries, idempotency, checkpoints and recovery;
- streaming/partial results;
- observability, logs and audit receipts;
- performance/resource limits;
- security/SSRF/path/injection defenses;
- lifecycle, versioning, deprecation and compatibility;
- UX and workflow integration;
- pricing/quota behavior and the reason the premium product exists.

## Representative patterns already translated

### MCP
MarkItDown -> bounded local document normalization.
Playwright + Chrome DevTools -> accessibility-oriented browser interaction separated from network/console/performance diagnostics.
Serena -> semantic symbol-level retrieval rather than flooding the model with raw source.
DBHub -> token-efficient, schema-aware database access with bounded results.
Basic Memory -> local-first versioned knowledge.
Context7 / Microsoft Learn -> revision-aware contextual documentation.
Official MCP 2026-07-28 -> stateless core, capability negotiation, lifecycle discipline and extension/deprecation model.
Tool annotations -> read-only/destructive/idempotent/open-world risk vocabulary.
Tasks/partial results -> candidate checkpointed asynchronous work and bounded partial-result semantics.

### GitHub Actions
Security-heavy Actions -> existing secret scanning, CodeQL, zizmor, Scorecard and Dependency Review.
AI/review Actions -> bounded AI analysis feeding deterministic acceptance rather than becoming the acceptance authority.
Build/release Actions -> Foundation-owned immutable release orchestration.
Caching/artifact Actions -> bounded cache/artifact use and provenance receipts.
Matrix/fan-out Actions -> parallel language and research lanes with cancellation and resource caps.
Performance Actions -> local benchmark contracts and measured resource evidence.
Cloudflare Actions -> Cloudflare deployment remains behind the canonical Foundation authority boundary.

### GitHub Apps
Security Apps -> native repository scanning and policy checks.
AI review Apps -> supervisor + deterministic PR checks.
Project-management Apps -> GitHub Issues/mission state remains canonical.
Observability Apps -> runtime receipts, artifacts and continuity checks.
Deployment Apps -> canonical deployment remains Foundation/Cloudflare-owned.

## Economic disposition

A discovered feature receives one of:

`native_free`
`composed_free`
`self_hosted_open_source`
`free_quota_bounded`
`paid_direct_forbidden`
`paid_feature_reimplement`
`research_only`

`paid_direct_forbidden` means the original service cannot enter runtime. It **does not** mean the feature is ignored. Its useful public behavior is a candidate for `paid_feature_reimplement`, `composed_free`, or another safe route.

## Implementation rule

We reproduce concepts and compatible functional behavior. We do not copy proprietary source code or protected assets without a compatible license.

## Promotion gate

`provenance -> gap analysis -> $0 disposition -> license/IP check -> contract -> deterministic test -> security/policy -> resource measurement -> differential/parity -> shadow -> canary -> rollback -> single authority`

## Current native-equivalence strategy

| Premium pattern | Project-native route |
|---|---|
| Premium web search | multi-source search/fetch/extraction + provenance |
| Hosted crawler | direct HTTP/JSON-LD/HTML/browser escalation |
| Managed browser diagnostics | bounded browser + runtime evidence |
| AI code review | advisory analysis + deterministic checks |
| Security SaaS | native secret/code/security scans |
| Managed memory | repository-owned versioned memory |
| Hosted documentation intelligence | revisioned repository/doc indexes |
| SaaS observability | receipts/artifacts/continuity checks |
| Project management SaaS | GitHub Issues + mission state |
| Cloud deployment SaaS | Foundation/Cloudflare authority |
| Premium database tooling | schema-aware bounded queries |
| Async task platform | checkpointed idempotent job/receipt lifecycle |

## Acceptance

- all supplied MCP rows processed: yes
- all supplied Action rows processed: yes
- all supplied App rows processed: yes
- paid products ignored: no
- direct paid runtime dependencies added: no
- paid trials used: no
- Marketplace Apps installed for discovery: no
- first-party Operations App retained: yes
- immutable Action allowlist retained: yes
- one authority per responsibility retained: yes