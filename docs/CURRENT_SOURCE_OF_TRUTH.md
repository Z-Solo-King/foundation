# Current Source of Truth — Foundation (public-safe)

This document is the public continuity authority for Foundation. Dated status/audit snapshots are historical evidence only.

Checked: 2026-09-29.
Continuity CI uses a full-depth Foundation checkout so merge-commit parent resolution remains valid.
Release continuity note: production acceptance namespaces are derived from GitHub's authoritative run-attempt value to prevent rerun receipt collisions.
Foundation main code checkpoint: 510b03b2ee2461c97b1c774349d08e3220985cce.
Operations main checkpoint: af3dc60349ca9de7c3747625949269234d34021f.
Production Operations pin: ce4f9edbae3ddf1bf1c25a908d5bce014acc7676.
Research Operations pin: 8bee0ca4c41e02d2b7005589a73f53dc0512aa9d.
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
