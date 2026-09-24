# Live GitHub + Cloudflare Sync Audit — 2026-09-24

## CURRENT LIVE CHECKPOINT — 2026-09-24 11:43 UTC

- Foundation `main`: `adb4bd994cd24b17d018e22dc22a5516da65b4c8` (PR #1101 merged).
- Operations `main`: `44f53283aa308e8a294ae9fe716ab9200a44809b`.
- Production Operations pin: `1a12b98981f52de207fa8626cf2e1f5ad06659be`.
- Nightly research / migration-review Operations pin: `44f53283aa308e8a294ae9fe716ab9200a44809b`.
- Open issues: 8 total — Foundation #58/#157; Operations #145/#340/#385/#597/#603/#699. Open PRs: 0.
- Post-merge Actions on the current Foundation `main`: Live chatbot production smoke run `35994616511` passed.
- Nightly research run `35994287754`, live canary `35994265831`, and provider preflight `35994265823` are blocked by the Worker-backed AI path: preflight reached HTTP 200 but returned `generation_status=deterministic_fallback` with no provider, while the local research proxy path returned HTTP 502. The nightly lanes therefore correctly recorded `blocked_before_execution`.
- The prior nightly shell quoting defect is fixed and the authenticated probe command is syntactically valid.
- `OPERATIONS_MIGRATION_TOOLS_REF` remains `41db817dee6aa7d369ea9a07dd072b58ece1695a` as a separate immutable tooling pin; Foundation tests explicitly require it to remain distinct from the canonical runtime research pin.
- Older dated sections below remain historical provenance and must not override this checkpoint.

## Current live synchronization — 2026-09-24

This snapshot records live GitHub/Cloudflare observations made during the audit. The repository heads below are the implementation/revision observations immediately before this documentation-only synchronization branch; merging this documentation branch may advance `main` without changing runtime code.

### Repository state

- Foundation `main` observed: `825d301d10d201cd9b74dd018973769aeb03f381`
- Operations `main` observed: `994793431981b87cd37f2ee1eabf8a2b11914c34`
- Production Operations pin: `1a12b98981f52de207fa8626cf2e1f5ad06659be`
- Nightly research / migration-review Operations pin: `41db817dee6aa7d369ea9a07dd072b58ece1695a`
- Open issues: 8 total — Foundation `#58/#157`; Operations `#145/#340/#385/#597/#603/#699`
- Open pull requests at audit start: 0
- Operations `#711` is closed and excluded from the active issue inventory; historical `#197` remains a regression case in the deep-scan corpus.

### Cloudflare production state

- Public Worker `research-intelligence-engine-public`: 100% on version `8e02eb65-344a-489e-ab11-7eb00db443b8`, GitHub provenance `825d301d10d201cd9b74dd018973769aeb03f381`.
- Public Worker release identity reports Foundation `825d301d10d201cd9b74dd018973769aeb03f381` and Operations `1a12b98981f52de207fa8626cf2e1f5ad06659be`.
- Private Worker `research-intelligence-engine-private`: 100% on version `e43463fd-4487-4248-94f0-503a405680cc`, GitHub provenance `1a12b98981f52de207fa8626cf2e1f5ad06659be`.
- Private Worker cron: `*/15 * * * *`.
- Public and private Workers share the production D1 boundary and intended service-binding relationship.
- Production release run `#501` completed successfully.

### Nightly research and artifact state

- Latest nightly run `#893` (run ID `35964787260`) prepared 24 programs across 3 lanes but was blocked before provider execution.
- The blocker is missing authorized `RESEARCH_LLM_ENDPOINT`, `RESEARCH_LLM_API_KEY`, and `RESEARCH_LLM_MODEL`; no provider-backed research findings were produced.
- Current nightly migration-review artifact `10794095266`: 40 migration-matrix cases + 24 capacity cases, 40 language-review rows, 3 repeats, 875 migration candidates, 1,371 source files, review score 70.0/100.
- The 24 capacity cases are `deterministic-structural` evidence with `runtime_performance_valid=false`; their zero-duration measurements must not be treated as runtime performance or answer-quality evidence.
- Nightly diagnosis artifact `10794105227` is current and correctly reports `blocked_before_execution`; older diagnosis artifact `10771684062` is historical and superseded.

### Latest benchmark / audit state

- Extractor benchmark `#362` (run ID `35964770398`) passed the strict evidence-quality gate with 40 receipts, provenance completeness 1.0, route-provenance completeness 1.0, repeat reliability 1.0, and zero unstable repeated groups.
- Its substantive result mix is 4 `ok`, 32 `empty`, 4 `blocked`; completion rate is 0.10 and error rate is 0.0. This is an evidence-contract pass, not a claim that 40 real acquisitions succeeded.
- Coverage-driven runtime matrix `#333` succeeded.
- Polyglot migration review `#117` succeeded.
- Open-issue deep scan `#365` (run ID `35964770241`) passed across four lanes, covering 8 active issues plus historical `Operations #197` (9 scan cases per lane); no failed cases were recorded.
- Deep-scan review findings are limited to lane/surface review conditions around Foundation `#157`; these do not constitute a new runtime failure.

### Current CI / contract problems

1. **Nightly provider gate:** live 24-program provider execution remains externally blocked by the three missing research-provider secrets.
2. **Production smoke contract mismatch:** latest smoke `#72` (run ID `35965101632`) fails because `live-chatbot-production-smoke.yml` posts diagnostic operation `infrastructure_verify`, while the current Foundation diagnostic contract/tests and production-release path expect `infrastructure_verify_public_test`. The live smoke returned HTTP 400 for that check; health, readiness, chat, SSE, research, storage and root checks returned HTTP 200.
3. **Centralized Operations validation:** scheduled validation `#24` (run ID `35964996777`) is red with a broad current test-suite compatibility/contract mismatch surface, including evaluation-receipt signature expectations, D1 fake batch-call expectations, WorkerEntrypoint test harness assumptions, provider/search routing expectations, public-core synchronization assertions, maintenance/activity tests, and related contract tests. This is a repository/CI problem separate from the successful production release.
4. These CI findings are current problems, not production outage claims. No runtime code or workflow was changed during this documentation reconciliation.

### Evidence boundary

`L0 hypothesis -> L1 source -> L2 repository -> L3 GitHub Actions/control-plane -> L4 approved runtime/production`

Repository inspection, deterministic tests, structural benchmark artifacts and historical receipts must not be represented as L4 runtime certification.


### Direct access verification

- GitHub authentication is working for the connected account.
- Both repositories are accessible with repository permissions reporting admin/maintain/push/pull/triage.
- Cloudflare account and Worker API reads succeeded for account metadata, Worker listings, Worker settings/bindings, schedules and deployments.
- Cloudflare write permissions were not probed by an unnecessary mutation.

### Synchronization conclusion

Production GitHub-to-Cloudflare provenance is aligned to the intended deployment boundary: Public Worker -> Foundation `825d301d...` + Production Operations `1a12b989...`; Private Worker -> Operations `1a12b989...`. The nightly research revision `41db817d...` is intentionally separate and is not expected on the production Workers.

