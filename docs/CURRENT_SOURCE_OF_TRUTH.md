# Current Source of Truth — Foundation (public-safe)

This document is the public continuity authority for Foundation. Dated status/audit snapshots are historical evidence only.

Checked: 2026-09-30.
Main verification checkpoint: current Foundation main is read live from GitHub; the last verified main commit is `f85b61ebc521dbfab3b25fa3b7fceafcf696cdbb`.
Continuity CI uses a full-depth Foundation checkout so merge-commit parent resolution remains valid.
Release continuity note: production acceptance namespaces are derived from GitHub's authoritative run-attempt value to prevent rerun receipt collisions.
Foundation main code checkpoint: current main is read live from GitHub; last verified commit `f85b61ebc521dbfab3b25fa3b7fceafcf696cdbb`.
Operations main checkpoint: current protected main revision is read from GitHub live state; research/migration jobs use explicit immutable pins below.
Production Operations pin: ce4f9edbae3ddf1bf1c25a908d5bce014acc7676.
Provider fleet runtime probe pin: b95e419254a9071beaeef57a1b0da22ba7dd2c4f.
Research Operations pin: 1a91efa53b9202f1624ddde892b0e86bd6b360f0.
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

The canonical public path is Pages `ai` -> `heroic` -> private `operations-edge` / `operations`. Production task-envelope signing uses the private `TASK_SIGNING_ROOT`; the bearer `AUTH_TOKEN` is a separate runtime authentication secret. D1 migrations 0001–0010 are live and verified.

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

Cross-repository continuity requires this document and docs/FAMILY_SYNC_STATE.json to be refreshed whenever canonical worker/workflow boundaries change.


## 2026-09-30 AI provider fleet
The current Foundation external AI API fleet is defined in `docs/AI_PROVIDER_FLEET_2026-09-30.md` and `docs/AI_PROVIDER_FLEET_2026-09-30.json`: OpenRouter, Groq, Gemini, NVIDIA NIM, Cohere, Hugging Face, and SiliconFlow. Cloudflare Workers AI is the native runtime inference binding. Operations privately supports Cerebras as an additional provider family, but Foundation does not activate it because no Cerebras credential is configured. Mistral is not part of the production provider fleet.
## 2026-09-30 live-state synchronization model
Current GitHub main revisions and mutable issue/PR counts are live state. This document records the last verified revision but deliberately does not pretend to contain a permanent current SHA. Refresh GitHub before mutation or production claims.

Current family state: Foundation and Operations are the only active repositories. The former standalone extractor-mapper repository is retired/deleted; active private extraction/mapping runtime is Operations `extractor_mapper/`, while Foundation retains the public deterministic mapper core.

The adaptive multi-lens engine is active on Foundation and is scheduling-only; it does not transfer acceptance, security, provider, resource, extractor/mapper or promotion authority.

## 2026-10-01 internal access / private Operations control refresh

Live verification on 2026-10-01 established:
- Foundation `main`: `f43028ca6c6a4f4d3cecbfdb99ae4602330228b4`.
- Operations `main`: `37b35ba9e94600d746bc81e48cd2918b0c239bc7`.
- Approved production Operations pin: `90fa37df10d63824acd3fe20b64cc91043af9627`.
- Cloudflare production annotations: `heroic` and `heroic-core` carry Foundation `f43028ca6c6a4f4d3cecbfdb99ae4602330228b4`; `operations` and `operations-edge` carry Operations `90fa37df10d63824acd3fe20b64cc91043af9627`.
- Operations `main` is intentionally ahead of the approved production pin. This is recorded as integrity drift until a reviewed promotion updates the immutable approval manifest.
- Cloudflare Worker topology exposes `heroic -> heroic-core`, `heroic-core -> operations-edge`, `operations-edge -> operations`, plus the protected D1/B2/AI bindings documented in `docs/INTERNAL_ACCESS_CAPABILITY_POLICY.md`.
- The private Operations repository does not have native protected-main enforcement on the current GitHub Free plan. The compensating control is the Foundation-hosted immutable approval manifest plus the 15-minute private-integrity guard.

