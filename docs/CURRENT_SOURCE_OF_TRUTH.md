# Current Source of Truth — Foundation (public-safe)

This document is the public continuity authority for Foundation. Dated status/audit snapshots are historical evidence only.

Checked: 2026-10-01.
Main verification checkpoint: current Foundation main is read live from GitHub; the last verified main commit is `139cbea93cb876889b234f28fc2bdc8b3b669fdd`.
Continuity CI uses a full-depth Foundation checkout so merge-commit parent resolution remains valid.
Release continuity note: production acceptance namespaces are derived from GitHub's authoritative run-attempt value to prevent rerun receipt collisions.
Foundation main code checkpoint: current main is read live from GitHub; last verified commit `139cbea93cb876889b234f28fc2bdc8b3b669fdd`.
Operations main checkpoint: current protected main revision is read from GitHub live state; current main is `2133534f9512eee4df49d78f6c39530502944b74`. Research and migration jobs use explicit immutable pins below.
Approved production Operations pin: `6042cb8cd972ba25d42ebebddcb763b9dfb57b67`.
Live production observed revision remains separately tracked by the release-evidence state; a fresh canonical certification is required after this pin change.
Provider fleet runtime probe pin: `b95e419254a9071beaeef57a1b0da22ba7dd2c4f`.
Research Operations pin: `1a91efa53b9202f1624ddde892b0e86bd6b360f0`.
Live issue and PR counts must be read from GitHub; this file never serves as a mutable queue.

## Public architecture

ai-cio.pages.dev is the canonical public front door.
Foundation owns public-safe contracts/core, the public edge/API, GitHub Actions, frontend and deployment orchestration.
The protected Operations side owns private runtime policy, provider control, resource governance, memory, recovery and protected tooling.
The retired extractor-mapper repository is historical material, not a runtime owner.

## Runtime and evidence boundary

Protected runtime revisions, resource identifiers, deployment internals, private issue state and private provider configuration are intentionally omitted from this public checkpoint.
Fresh production/runtime evidence must be obtained from the protected evidence path before making an L4 claim.

Current evidence classes:
- Nightly 24-program research: no provider-backed closure receipt is currently certified.
- Extractor/feed evidence: native retailer-hosted feed evidence remains required for #1247/#1249.
- Polyglot migration: deterministic/structural evidence exists; runtime performance/evidence remains required before promotion.

## Acquisition source selection

Acquisition is adaptive: browser retrieval, direct HTTP/HTML, public APIs, feeds, structured page data and search discovery are valid source modes when available. A failed transport is not automatically a failed data target; change acquisition mode when another configured route can expose the requested data. Preserve source provenance and acquisition mode.

## Connector / session continuity

GitHub and Cloudflare are separate evidence surfaces, not separate product architectures.
A session may use both when both connectors are active. When connector availability is isolated or unreliable, use the corresponding separate chat/lane; workflow dispatch input semantics must still be verified explicitly.
Conversational expectations are never runtime evidence.
The current Foundation execution policy is docs/AI_AGENT_EXECUTION_POLICY.md.

## Queue integrity

Use GitHub live state, not this document, for current issue/PR counts after the checkpoint.
Use canonical-authority clustering and cross-fire validation for implementation work.
Do not create duplicate authorities for admission, URL/SSRF safety, evidence, routing, research execution, or deployment.

## Runtime authority note

The canonical public path is Pages `ai` -> `heroic` -> private `operations-edge` / `operations`. Production task-envelope signing uses the private `TASK_SIGNING_ROOT`; the bearer `AUTH_TOKEN` is a separate runtime authentication secret. D1 migrations 0001–0010 are live and verified. Foundation-owned feed-hunt CI is a public-read-only evidence workflow; it does not grant private production authority.

## Continuity

Use this file together with docs/FAMILY_SYNC_STATE.json and docs/PROMPT_TO_CANONICAL_DOC_MAP.md.
Production diagnostic acceptance passes the explicit `release_acceptance` mode through the public-to-private diagnostic boundary; this path is validated by the canonical production release. 
Do not add another competing current-state document.


### 2026-09-29 runtime repair note
The canonical production release runtime now passes the authenticated infrastructure diagnostic on the current production pair. The remaining release failure was in the post-release nightly workflow-dispatch command: GitHub CLI requires JSON workflow inputs on stdin when using --json. Foundation PR #1549 corrects that dispatcher contract and adds regression coverage; runtime authority and feed extraction scope are unchanged.


## 2026-09-29 dispatch contract refresh
The canonical production release dispatches live nightly research with typed string workflow inputs (`dry_run=false`, exact Foundation SHA, exact production release run ID). Production smoke tracks the production Operations pin; research preflight and research execution retain their separate immutable research pin.


## 2026-09-29 authenticated provider-proof repair
The live post-release test exposed a contract distinction: ordinary public chat intentionally redacts provider identity, while the authenticated nightly evidence path must preserve provider provenance. Foundation PR #1559 adds the explicit research-proof header path, supports the existing private `provider_runtime_verify` diagnostic operation at the authenticated boundary, and corrects false-positive preflight classification. Ordinary public responses remain provider-redacted.


## 2026-09-29 provider diagnostic status repair
Foundation PR #1562 aligns the public authenticated diagnostic wrapper with the dedicated `provider_runtime_verify` response contract. A valid provider runtime receipt no longer requires the unrelated generic `chatbot.allowed` field; ordinary infrastructure diagnostics retain that requirement.

### 2026-09-30 nightly evidence hardening
Foundation PR #1565 hardens nightly research using the feed-recovery evidence pattern: provider capability preflight exercises the actual research-agent structured-output contract; exact 24-program coverage records missing, duplicate, and unexpected IDs; transient upstream transport recovery is bounded and preserves request identity; and machine-readable acceptance manifests map evidence to #58/#157/#597/#603. The migration review pin now uses the merged Operations PR #1109 bridge repair commit `f9f8ce0eb88b92a5d4e2e3ea5f2d397eebac5791` rather than the older pre-repair audit revision.
## 2026-09-30 research boundary repair

Foundation PR #1573 fixes a live nightly research contract defect exposed by the production-live run: the CI research proxy had placed the private Operations research_agent capability inside the public ChatRequest JSON payload, which correctly failed public schema validation. The corrected boundary keeps ChatRequest closed, uses the authenticated X-Heroic-Research-Proof: 1 header as the capability signal, and adds research_agent=true only when Foundation forwards an authorized knowledge request to private Operations.

The PR was merged at 732a694cf2e272709640c379d9aed70ea28b2534. The canonical production release for that revision is separately tracked; no production-live research acceptance is claimed until the release dispatch and a fresh 24-program run pass.

Cross-repository continuity requires this document and docs/FAMILY_SYNC_STATE.json to be refreshed whenever canonical worker/workflow boundaries or integration contracts change.


## 2026-09-30 AI provider fleet
The current Foundation external AI API fleet is defined in `docs/AI_PROVIDER_FLEET_2026-09-30.md` and `docs/AI_PROVIDER_FLEET_2026-09-30.json`: OpenRouter, Groq, Gemini, NVIDIA NIM, Cohere, Hugging Face, and SiliconFlow. Cloudflare Workers AI is the native runtime inference binding. Operations privately supports Cerebras as an additional provider family, but Foundation does not activate it because no Cerebras credential is configured. Mistral is not part of the production provider fleet.
## 2026-09-30 live-state synchronization model
Current GitHub main revisions and mutable issue/PR counts are live state. This document records the last verified revision but deliberately does not pretend to contain a permanent current SHA. Refresh GitHub before mutation or production claims.

Current family state: Foundation and Operations are the only active repositories. The former standalone extractor-mapper repository is retired/deleted; active private extraction/mapping runtime is Operations `extractor_mapper/`, while Foundation retains the public deterministic mapper core.

The adaptive multi-lens engine is active on Foundation and is scheduling-only; it does not transfer acceptance, security, provider, resource, extractor/mapper or promotion authority.

### 2026-10-01 cohesion + decomposition reconciliation
The project-wide integration contract is now bound to the improvement matrix and explicitly connects audit, quality/evolution, learning, AI automation, AI API governance, evidence, self-evolution, and mapper/extractor without creating duplicate authorities. Operations also restores the evaluation-receipt to universal-evolution bridge and keeps learning candidate-only.

The first large-file decomposition wave split Operations `runtime_language_policy.py` into language-fit, migration-artifact, and AI-maintainability modules while retaining the original import surface. A second split extracted the large Operations infrastructure diagnostics orchestration into `control_plane_infrastructure.py`; the route/compatibility facade remains `control_plane_diagnostics.py`. Source-surface auditing treats >50,000 bytes or >1,000 lines as critical and >25,000 bytes or >500 lines as attention.

## 2026-10-01 hosted CI authority reconciliation
Foundation remains the sole hosted GitHub Actions authority for the family. The WooCommerce 32-site public feed-hunt capability remains implemented in Operations (`tools/woocommerce_32_plugin_feed_hunt.mjs`), but its hosted CI workflow was retired from Operations and is now executed by the Foundation-owned `.github/workflows/woocommerce-32-plugin-feed-hunt.yml` at an immutable Operations revision. Operations main contains no hosted GitHub Actions workflow after this reconciliation.

### 2026-10-01 Marketplace App indirect implementation
The 1,408 supplied GitHub Marketplace App records were analyzed as capability patterns rather than installation requests. Foundation now maintains a capability catalog and an App policy v2 boundary: Marketplace installation remains disabled, while the first-party Operations access App is explicitly limited to the Operations repository and `contents: read`. Foundation CI validates its usage across workflows. No external Marketplace App is a runtime dependency.


### 2026-10-01 hybrid & alternative capability-mining reconciliation
The project-wide $0 model now treats paid, premium, hosted and proprietary ecosystems as research inputs rather than exclusion lists. The supplied MCP, GitHub Actions Marketplace, and GitHub Apps datasets are covered by `docs/HYBRID_ALTERNATIVE_ECOSYSTEM_AUDIT_2026-10-01.*`, while direct paid runtime dependencies remain forbidden. Useful public behavior, architecture, policy, resource controls, lifecycle semantics and UX may be reimplemented using native GitHub/Cloudflare capabilities, open-source components, or bounded documented free quotas subject to deterministic, security, resource, provenance, shadow, canary and rollback evidence.

## 2026-10-01 autonomous control-plane acceptance

The v1 autonomous engineering supervisor is independently scheduled and is not a ChatGPT/session dependency. Live hosted evidence includes provider runtime-state publication (run 36844955035), child-run reconciliation into verifying (run 36845396455), deterministic fallback rotation (run 36845689035), and successful child workflow completion (run 36845712210). Production release remains outside autonomous workflow authority.

## 2026-10-01 provider/runtime acceptance

The provider fleet workflow is operational end-to-end. Run 36844955035 generated a sanitized provider runtime snapshot and published CHAT_PROVIDER_RUNTIME_STATE to the private Operations Worker. The current live probe records SiliconFlow as temporary with zero successful probes; provider admission therefore remains fail-closed rather than falsely promoted.

## 2026-10-01 production-release boundary

The privileged production workflow is now manual-only (workflow_dispatch). Ordinary Foundation main pushes and autonomous merges no longer trigger production deployment. The latest attempted release before that boundary (run 36846407025) deployed the Worker pair and passed Operations provenance/policy checks, but persistence acceptance failed because the Cloudflare account had exhausted the D1 free-tier daily row-read limit. That run is not a production certification.


## 2026-10-01 live family-state reconciliation

Current live issues: Foundation #58, #1247, #1249, #1672 and Operations #603 are the five acceptance-track items. Foundation autonomous mission/improvement issues and the Operations-main integrity drift issue remain live incident/execution state and are not folded into the acceptance matrix.

Foundation is the sole hosted Actions authority. Operations remains the private runtime, provider, resource, memory, extractor/mapper and policy authority. The project integration contract binds each improvement surface to audit, quality/evolution, learning and bounded AI automation while preserving existing security, identity, resource, provenance and promotion authorities.


## 2026-10-01 canonical Operations production pin promotion

The production Operations pin is now the merged revision `6042cb8cd972ba25d42ebebddcb763b9dfb57b67`, which includes the bounded D1 persistence-sentinel optimization from Operations PR #1437. Operations main remains a separate moving branch and is not production authority. The pin change is a cost-efficiency/control-plane change only; a fresh production deployment and runtime certification remain required before claiming production acceptance.

## 2026-10-01 final cohesion checkpoint

Foundation main: `282d7eae9fda93dcd4440bcf123f328a67a66a8d`.
Operations main: `3622efa5ba9d3639e8dd0998130a52cedada06f3`.

The current cohesion layer is bound to `docs/SYSTEM_INTEGRATION_CONTRACT.json` and `docs/PROJECT_IMPROVEMENT_MATRIX.json`. Audit, universal quality/evolution, learning, bounded AI automation, AI API/resource policy, evaluation evidence, self-evolution, and mapper/extractor controls are cross-cutting adapters rather than competing authorities. Evaluation receipts explicitly bridge into universal evolution scoring; incomplete metric vectors remain outside the learning loop.

The latest maintainability pass split the Foundation WooCommerce V175 harness into focused contracts, discovery/validation, acquisition/advisory, and orchestration modules while retaining the legacy import/CLI facade. Oversized-source detection remains enforced by the family coverage audit. Current large source surfaces are tracked in `docs/SOURCE_DECOMPOSITION_BASELINE_2026-10-01.md`; further decomposition is staged by responsibility rather than by arbitrary line cutting.

The live GitHub PR queue is the authority for current PR state. Feed-recovery PRs remain a separate evidence track and are intentionally not folded into this cohesion checkpoint.


## 2026-10-01 Operations syntax repair checkpoint

Operations main now includes the syntax repair from PR #1451 after centralized Foundation validation exposed two malformed refactor artifacts. The universal method-effectiveness bridge remains in its dedicated adapter; the legacy method-effectiveness compatibility module is valid again. The exhaustive-audit autofix module no longer contains an incomplete entrypoint stub. This repair is structural and does not change promotion authority.

## 2026-10-01 live feed-workflow deconfliction

Foundation main `68aff623472af4df03688ddb24f33259d1fe5532` and Operations main `942eb72d1df90299d52977918dd56e9d25e0c41f` include the current WooCommerce V18 feed-recovery deconfliction and Common Crawl pacing repairs. Legacy native-feed and clean-recovery harnesses are manual-only compatibility surfaces; the current V18 executor remains the canonical feed-recovery authority. These changes are feed-track state and do not alter the public/private runtime authority model.

## 2026-10-01 private Operations integrity-input generation repair

Foundation main `2239ae23706e5ab14c61869022eca93618b74cb9` contains the repaired Operations private integrity guard. The workflow now constructs its validator input with `jq -n`, preventing empty-stdin JSON generation and preserving the fail-closed comparison against the immutable approved Operations production revision. The repair changes no authority, credential, policy, or deployment boundary.

## 2026-10-01 final live reconciliation
Foundation main is `139cbea93cb876889b234f28fc2bdc8b3b669fdd`; Operations main is `2133534f9512eee4df49d78f6c39530502944b74`. No Foundation or Operations pull requests remain open. Superseded autonomous missions and stale feed recovery PRs were retired; runtime/evidence issues remain open until their stated gates are actually satisfied. The current live WooCommerce V18 and emergency 30-way recovery runs are evidence work and are not treated as completed merely because their workflows started.