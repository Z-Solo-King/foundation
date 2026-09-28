# Foundation continuity archive — 2026-09-28

Historical public-safe continuity records consolidated from root documentation. Live repository/runtime state is authoritative; these sections exist for provenance only.

---

# SOURCE: docs/CHATGPT_SESSION_OBSERVATIONS.md

# 2026-09-25 POST-MERGE LIVE AUDIT OVERRIDE

This is the current post-merge source-of-truth snapshot.

- Foundation main: e6514890548278e26331269e4abb0818b119233a
- Operations main: [REDACTED-OPERATIONS-SHA]
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs: 2 — Operations #914/#915 (Dependabot development dependencies). Foundation has none. No project implementation PR remains open.
- Repository fixes merged in this cycle: Foundation #1194, #1196, #1197, #1198, #1199, #1200, #1201, plus documentation #1195.
- Latest clean family-integrity run on corrected main: 36119501613 PASS.
- Latest production run 36119501519: FAIL only at Cloudflare zone activation prerequisite after 1040 repository tests and Cloudflare account/D1 authorization checks passed.
- Latest provider preflight 36119501717: FAIL CLOSED on DNS — HTTP 000, curl exit 6, dns_or_network_unreachable.
- Latest public Worker live probe 36119501481: FAIL at the same public-domain DNS boundary.
- Latest completed extractor benchmark remains run 36118106992, artifact 10855896489, digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d; 40 receipts, 4 ok / 32 empty / 4 blocked, provenance 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable groups, 0 invalid resource rows, 0 missing key rows.
- Active nightly run 36119514469 remains behind the exact production gate; no provider-backed 24-program acceptance receipt is certified.
- Cloudflare account role: [REDACTED-CF-ROLE]. Zone [REDACTED-CUSTOM-DOMAIN] remains pending/unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance [REDACTED-OPERATIONS-PROVENANCE-SHA].
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

Current verified cross-surface snapshot. Live workflow receipts and Cloudflare control-plane state outrank older dated sections.

- Foundation main: f7f824fde15e66d6ec6b4c9065feed124a1ce78d
- Operations main: [REDACTED-OPERATIONS-SHA]
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs at audit snapshot: Foundation #1195 (this documentation reconciliation); Operations #914/#915 (Dependabot). No implementation PR remains open.
- Merged repairs in this cycle: #1194 Cloudflare release authentication header; #1196 nightly preflight network diagnostics; #1197 dual GitHub-token family scan; #1198/#1199 family issue-key normalization; #1200 truthful cancelled-lane nightly fan-in; #1201 canonical nightly workflow structure.
- Family integrity on corrected main: run 36119000013 PASS.
- Production run 36119000062 FAIL: 1040 repository tests and Cloudflare account/D1 authorization checks pass; release stops only because [REDACTED-CUSTOM-DOMAIN] is not an active Cloudflare zone.
- Provider preflight 36118999990 FAIL CLOSED: HTTP 000, curl exit 6, dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev.
- Latest completed extractor benchmark: run 36118106992; artifact 10855896489; digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d; 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; 0 unstable groups; 0 invalid resource rows; 0 missing key rows.
- Current nightly run 36119013418 remains behind its exact production gate; no provider-backed 24-program acceptance receipt is certified.
- Cloudflare account: [REDACTED-CF-ROLE]; [REDACTED-CUSTOM-DOMAIN] pending/unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance [REDACTED-OPERATIONS-PROVENANCE-SHA]; D1 [REDACTED-PRIVATE-D1] ID [REDACTED-D1-ID].
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare runtime receipts are authoritative.
- No runtime or production issue is considered closed without its required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub/Cloudflare evidence outranks older checkpoint values below.

- Foundation main: 6b43bafa0f1d298e9a1a2c84b6721bb1eea4d0ac
- Operations main: [REDACTED-OPERATIONS-SHA]
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: Foundation #1195; Operations #914/#915. No implementation PR remains open.
- Repository fixes merged this cycle: #1194 (Cloudflare release auth), #1196 (nightly preflight diagnostics), #1197 (dual family tokens), #1198/#1199 (family issue-key normalization), #1200 (truthful nightly fan-in for cancelled lanes).
- Current production release 36118107525: FAIL at the Cloudflare zone prerequisite after repository and Cloudflare account/D1 authorization checks passed. [REDACTED-CUSTOM-DOMAIN] is not an active Cloudflare zone in the configured account.
- Current preflight 36118107000: FAIL closed with HTTP 000, curl exit 6, dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev; no diagnostic parser crash.
- Current family integrity 36118107049: PASS after the final family normalization repair.
- Newest completed live extractor benchmark: run 36118106992 on Foundation 70093db3; artifact 10855896489; digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d. Direct artifact inspection confirms pass=true, 40 receipts, 0 invalid resource rows, 0 missing key rows, provenance completeness 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable repeated groups, status 4 ok / 32 empty / 4 blocked, recovery rate 1.0.
- Latest nightly multi-agent cycle is correctly gated before provider execution because production is not certified; there is no new provider-backed 24-program acceptance receipt from this environment.
- Cloudflare account role: [REDACTED-CF-ROLE]. Zone [REDACTED-CUSTOM-DOMAIN] remains pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance remains github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance remains [REDACTED-OPERATIONS-PROVENANCE-SHA]; D1 [REDACTED-PRIVATE-D1] ID [REDACTED-D1-ID].
- Canonical Worker subdomains are disabled; do not create a competing public authority to bypass the requested [REDACTED-CUSTOM-DOMAIN] domain.
- ChatGPT/UI state is transport state only; GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.
- No runtime or production issue is closed without the required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub and Cloudflare evidence outrank older checkpoint values below.

- Foundation main: 70093db359570b3f87d135e26b525645135fa517
- Operations main: [REDACTED-OPERATIONS-SHA]
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: 3 — Foundation #1195 (this documentation reconciliation); Operations #914/#915 (Dependabot development-dependency updates). No implementation PR remains open.
- Foundation PRs #1194, #1196, #1197, #1198, #1199 fixed confirmed Cloudflare-release/family-integrity/preflight defects and are merged.
- Current production release 36118107525: FAIL at the Cloudflare zone prerequisite after repository and Cloudflare account/D1 authorization checks passed. [REDACTED-CUSTOM-DOMAIN] is not an active zone in the configured account.
- Current provider preflight 36118107000: FAIL closed with truthful transport evidence — HTTP 000, curl exit 6, network_classification dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev. No parser crash.
- Current family integrity 36118107049: PASS.
- Latest completed extractor benchmark 36115560009: PASS; artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e; 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; unstable repeated groups 0.
- The newer current-main extractor benchmark (36118106992) has not yet produced a completed replacement artifact; retain 36115560009 as the latest completed benchmark.
- Cloudflare account role: [REDACTED-CF-ROLE]. Zone [REDACTED-CUSTOM-DOMAIN] remains pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance is github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance is [REDACTED-OPERATIONS-PROVENANCE-SHA]; D1 [REDACTED-PRIVATE-D1] ID is [REDACTED-D1-ID].
- Nightly multi-agent research is correctly blocked behind the exact production gate; no provider-backed 24-program receipt is certified.
- ChatGPT/UI state is transport state only; GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.
- No runtime or production issue is closed without its required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub and Cloudflare evidence overrides older checkpoint values below.

- Foundation main: 6eb531095148cb6657bccc72a64542691dbb6fa1
- Operations main: [REDACTED-OPERATIONS-SHA]
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: Foundation #1195; Operations #914/#915. Older duplicate implementation/documentation PRs #1186/#1187/#951 are closed as superseded.
- Production release 36117585242 is the current fresh run; the prior current-head run was blocked because [REDACTED-CUSTOM-DOMAIN] is not an active Cloudflare zone.
- Provider preflight 36117585207 is the current fresh run; the immediately prior corrected preflight recorded HTTP 000 / curl exit 6 / DNS resolution failure without crashing.
- Family integrity 36117585223 is the current fresh run after the dual-token fix; the previous failure was traced to using a private Operations-only token for the Foundation public issue inventory.
- Latest completed extractor benchmark 36115560009 passed the strict integrity gate: 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; 0 unstable groups. Artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e.
- Cloudflare account access: [REDACTED-CF-ROLE]. Zone [REDACTED-CUSTOM-DOMAIN] is pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance [REDACTED-OPERATIONS-PROVENANCE-SHA]; D1 [REDACTED-PRIVATE-D1] ID [REDACTED-D1-ID].
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare runtime receipts are authoritative.
- No runtime/production closure is asserted without the required live receipt.

---

# 2026-09-25 CURRENT LIVE AUDIT OVERRIDE

This section supersedes older dated checkpoint values for current-state interpretation. GitHub live refs and Cloudflare runtime receipts are authoritative.

- Foundation main at this audit snapshot: 01bfa0c6a74bf6f10082ac8034aa1b2d098d0e42.
- Operations main at this audit snapshot: [REDACTED-OPERATIONS-SHA].
- Open issues: 10 total — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs after duplicate cleanup: Foundation #1194; Operations #914/#915. Foundation #1193 merged the family-state/acceptance-matrix reconciliation; Foundation #1186/#1187 and Operations #951 were superseded/closed.
- Production release 36115559861 failed at Cloudflare API error 6111 (invalid Authorization header format during zone lookup). Current-head production is not certified.
- Nightly preflight 36115559932 failed with public Worker HTTP 000; nightly 36115573281 was cancelled by the exact production gate. No new provider-backed 24-program receipt exists.
- Live extractor benchmark 36115560009 passed: 40 receipts, provenance 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable groups, 4 ok / 32 empty / 4 blocked. Artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e.
- Cloudflare: account role [REDACTED-CF-ROLE]; [REDACTED-CUSTOM-DOMAIN] pending with activation failure reason unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]; deployed Operations provenance [REDACTED-OPERATIONS-PROVENANCE-SHA]; D1 [REDACTED-PRIVATE-D1] ID [REDACTED-D1-ID].
- Current Foundation main family-integrity workflow already uses actions/create-github-app-token and current main no longer contains the closed operations#352 target.
- ChatGPT/UI state is transport state only. Use this override as the cross-chat continuation point and refresh live refs before mutation.

---

# 2026-09-24 FINAL POST-SYNC OBSERVATION

- Cycle 7 documentation PRs #1137 and #896 are merged.
- At the post-merge verification point there are 8 open issues and 0 open implementation PRs.
- Production remains pinned to Foundation `725e1b9cdaa637f07d4264673cddfc8ab806b3c6` + Operations `[REDACTED-OPERATIONS-SHA]`; production release `36030977718` is PASS for that exact pair.
- Nightly research `36030996071` and canary `36030977932` remain blocked by the upstream public Worker HTTP 403 / local HTTP 502 boundary.
- Cloudflare basic control-plane access is verified; exact deployment-history/version freshness remains a separate receipt and is not inferred.
- Current repository documentation should be treated as a compact checkpoint, while fresh `main` refs must be queried before mutation.

---

# Cycle 7 — 2026-09-24 — live cross-surface reconciliation

- Current GitHub heads: Foundation `2710b7559c9c7a0dcd2c84fe6ed77b8dbc684706`; Operations `[REDACTED-OPERATIONS-SHA]`.
- Current queue: 8 open issues and 1 open documentation PR (#1137); no open implementation PRs.
- Production release `36030977718` passed using Foundation `725e1b9cdaa637f07d4264673cddfc8ab806b3c6` and Operations production pin `[REDACTED-OPERATIONS-SHA]`.
- Nightly research `36030996071` and canary `36030977932` remain blocked by the same upstream public Worker HTTP 403 / local 502 boundary.
- Cloudflare account membership, Worker listing and D1 listing were successfully read during this audit. The connector is available; the remaining unverified item is a fresh deployment-history/version/provenance read, not basic access.
- The project documentation must distinguish: current GitHub branch heads; immutable production pins; fresh Cloudflare runtime receipts; and historical continuity notes.
- The conversation/UI is not authoritative for backend execution. Use GitHub/Cloudflare receipts, commits and workflow runs as the execution ledger.

---

# ChatGPT Session Observations

**Observed:** 2026-09-24

# Cycle 5 observations — 2026-09-24

- This observation cycle is intentionally being run with the ChatGPT Android app kept open rather than closed/backgrounded. That creates a useful controlled contrast with earlier cycles, but it is not by itself proof that app closure causes backend/connector execution to stop.
- Current research across OpenAI's Help/Status material, OpenAI Community, Reddit, GitHub/Codex issues, mainstream technical coverage, and searched Chinese-language communities supports a broader pattern of long-chat/mobile state or message-stream instability. OpenAI's troubleshooting guidance explicitly recommends starting a new chat for long or many-turn conversations and restarting the app for lag/freezing; the status history also records September 23, 2026 mobile and Conversation incidents. Community and Reddit reports include Android "Error in message stream", long-chat freezing/stalling, stale or unsynchronized mobile views, and GPT-5.6 Sol/Thinking-specific complaints. These are reports and troubleshooting signals, not proof of one shared root cause.
- GitHub/Codex reports are particularly relevant to this project's workflow shape: Android/Desktop remote sessions have been reported to show stale state or reasoning-effort mismatches while host-side work exists, which supports treating the visible mobile conversation as non-authoritative for backend progress.
- Chinese-language searches (Zhihu, Baidu Tieba, Douban, PTT, Bilibili) produced sparse or generic indexed results for this exact failure mode. No strong platform-specific evidence was found there that would justify a stronger causal claim.
- Engineering rule for this project: keep heavy GitHub/runtime work resumable, prefer exact run IDs and compact checkpoints, avoid continuous polling/large log dumps, and treat repository/control-plane receipts as authoritative even when the mobile UI is stale.
- When the app remains open, continue observing whether responsiveness improves or deteriorates before the adaptive early-checkpoint threshold. Record the actual observed outcome in the next checkpoint rather than assuming the result.

Useful external references:
- OpenAI troubleshooting: https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages
- OpenAI status history: https://status.openai.com/history
- OpenAI Community Android message-stream report: https://community.openai.com/t/chatgpt-android-error-in-message-stream-interrupts-long-conversations/1399948
- Reddit GPT-5.6 Sol issues: https://www.reddit.com/r/ChatGPT/comments/1w8ebl6/gpt_56_sol_issues/
- Reddit current slow/unresponsive Sol report: https://www.reddit.com/r/ChatGPT/comments/1wokavg/chatgpt_has_been_slow_and_completely_scuffed_for/
- GitHub/Codex Android reasoning sync report: https://github.com/openai/codex/issues/42301


## Cycle 4 observations — 2026-09-24

- The user reported that this ChatGPT session also became unresponsive. They observed that closing the ChatGPT app and later returning can coincide with repository work having continued, so the foreground mobile conversation state and backend/tool execution may not always fail at the same boundary. This is an observed behavior, not a proven causal diagnosis.
- Current external evidence is consistent with session/thread synchronization and long-chat UI problems: OpenAI's current troubleshooting guide specifically recommends starting a new chat for long/many-turn conversations and restarting the app for lag/freezing. OpenAI Community reports from September 2026 describe long Android chats remaining visibly stale until force-close/reopen, and GPT-5.6 Thinking long requests ending with message-stream failures after several minutes. These reports are supporting context, not proof of the cause of this project session.
- The engineering implication is to keep work resumable and compact: checkpoint before context pressure, avoid large log dumps, use targeted reads, do not continuously poll long-running workflows, and treat app/UI freshness separately from authoritative GitHub runtime state.
- The current project cycle therefore uses an adaptive early checkpoint rule: if responsiveness degrades before the 20-minute ceiling, stop launching new expensive work and resume from the latest repository checkpoint in a fresh chat.

## Session execution observations

- Work was performed as a bounded engineering session rather than an unbounded scan/fix/poll loop.
- The conversation had accumulated stale checkpoints and large historical issue bodies; refreshing only the current head and current open-issue surface reduced noise.
- Parallel independent reads were materially more efficient than serially reopening every issue.
- A concrete repository defect was identified quickly from the current checkpoint: the chatbot smoke history reported `infrastructure_verify` versus `infrastructure_verify_public_test`. Current `main` already contains the corrected workflow contract, so no duplicate code fix was made.
- The nightly canary's failure-receipt path was found to lose structured evidence on pre-receipt failures. That was repaired so Worker HTTP status and bounded error fields are preserved.
- CI pile-up was identified as an execution-speed risk. Five expensive, supersedable Foundation workflows now cancel stale runs.
- GitHub and Cloudflare are permitted in one cycle by policy. In this session, the exposed tool registry did not provide an active Cloudflare action, so Cloudflare state was not claimed as freshly verified.
- Runtime/evidence gates were kept separate from repository defects; no issue was closed merely from deterministic CI evidence.

## Session safety rule

- **Project session cap: 20 minutes.**
- Sustained execution commands should include: **"Keep going until completed, within the 20-minute session limit."**
- Near the session boundary, stop launching new expensive scans, write a compact checkpoint, and resume from that checkpoint in a fresh chat/cycle.
- Observe session behavior after each cycle and update this document with concrete bottlenecks and improvements.

## Current optimization strategy

**Parallel diagnosis -> one consolidated repair batch -> targeted verification -> checkpoint.**

Target 4 lanes by default; expand to 6 only when lanes are genuinely independent. Avoid continuous polling and avoid feeding complete logs into the chat.


## Cycle 2 observations — 2026-09-24

- Session remained responsive under bounded parallel reads and focused writes; no continuous workflow polling was used.
- Parallel diagnosis found two fresh confirmed Foundation CI defects beyond the prior checkpoint: PR #1129 fixed workflow-dispatch run identity tracking, and PR #1130 fixed the Hybrid URL corpus count plus an invalid Rust cache target. Both PRs had fresh required checks, exhaustive-audit checks, and nightly-contract checks passing before merge.
- Both repairs were merged during this cycle: #1129 -> `5ab5eb1c5fc4dc07c7e0a533bbfc402cb766d424`; #1130 -> `e541ac4d000ed4a0678aa1ef6ebe9faf6c119c0a`.
- Operations main advanced independently to `[REDACTED-OPERATIONS-SHA]` via the Rust HTML availability contract repair (#887); the stale cross-repository checkpoint was therefore no longer safe to reuse unchanged.
- The main execution bottleneck remains L4/runtime/provider evidence, especially the upstream Worker 403 blocking the 24-program research gate; repository-side CI defects are being reduced faster than runtime evidence can be refreshed.
- Improvement for the next cycle: refresh live heads and open queues first, then inspect only newly changed commits/PRs and current blockers. Reconcile the checkpoint after every consolidated repair batch.


## Cycle 3 final observation — 2026-09-24

- This cycle ran materially longer than the previously observed ~7-minute session; execution remained responsive through the bounded repair and verification sequence.
- Repository-side fixes completed: Foundation #1132 and #1134 merged; Operations #890 merged.
- #1134 fixed transient 404 workflow-job materialization handling, and fresh post-merge evidence confirms Fresh control-plane identity acceptance passed on Foundation 07ef89f3... and canonical bridge run 36029359126 passed with job 107733899066.
- Operations #890 fixed overlapping maintenance-lane claims so concurrent scheduler attempts deterministically deny instead of leaking SQLite primary-key conflicts.
- Broad Operations issue lanes remained evidence-gated rather than producing speculative code changes; current open issue count remains 8.
- No fresh Cloudflare runtime claim was made because the active Cloudflare action was not exposed to this chat.
- Session optimization result: bounded parallel diagnosis plus immediate targeted verification produced more verified progress than broad rescans. The remaining runtime/provider blockers should be resumed from the compact checkpoint rather than through continuous polling.


## Cycle 6 — 2026-09-24 — session/context boundary

- The current ChatGPT conversation became unresponsive again and then reached the practical chat/session limit. This confirms that a single long-running engineering conversation must be treated as disposable transport state, not as the continuity mechanism for project work.
- The user also observed a correlation between closing the ChatGPT Android app and the conversation becoming unavailable/unresponsive. Current evidence does **not** establish that force-closing the app either universally stops or universally preserves backend GitHub/runtime execution for ordinary Chat mode. Feature-specific behavior is documented separately by OpenAI, so repository evidence remains authoritative.
- External September 2026 research reviewed during this cycle: OpenAI Help/Status, OpenAI Community, Reddit, GitHub/Codex, mainstream technical coverage, and searches of Zhihu, Baidu Tieba, Douban, PTT and Bilibili. The strongest matching signals concern long-chat/mobile message-stream or synchronization instability; Chinese-language results were comparatively sparse/generic and did not justify a stronger causal claim.
- Reddit/community reports specifically include GPT-5.6 Sol/Thinking slow/stuck behavior, Android message-stream failures, and long-conversation freezing/stalling. These are community reports, not root-cause proof.
- OpenAI's current troubleshooting guidance recommends starting a new chat for long or many-turn conversations when ChatGPT becomes slow/frozen/stuck. The project should therefore checkpoint before the conversation becomes large rather than trying to preserve one continuous chat.
- Product terminology note: current OpenAI documentation describes GPT-5.6 Sol with reasoning levels such as Instant/Medium/High/Extra High; this project should not treat "Sol Light" as a formally documented product mode unless a current source explicitly establishes it.
- New operating rule: if responsiveness degrades, the app is closed during a heavy cycle, or the session reaches context/length pressure, stop launching expensive work, write a compact GitHub checkpoint, and continue in a fresh chat. Do not infer completion or failure from the mobile UI alone.
- This cycle's authoritative project state at checkpoint: Foundation main `2710b7559c9c7a0dcd2c84fe6ed77b8dbc684706`, Operations main `[REDACTED-OPERATIONS-SHA]`, 8 open issues, 0 open PRs, canonical production Operations pin `[REDACTED-OPERATIONS-SHA]`, canonical production release run `36030977718` PASS, latest nightly research run `36030996071` blocked by upstream Worker HTTP 403 (local HTTP 502 `upstream_worker_rejected`), and live nightly canary `36030977932` failed on the same boundary.
- Cloudflare control-plane state was not freshly verified in this chat because the dedicated Cloudflare action was not exposed. No new standalone Cloudflare deployment/version/binding/cron/secrets claim is made.


---

# SOURCE: docs/AI_ENGINEERING_CONTINUITY_LEDGER_2026-09-21.md

# AI Engineering Continuity Ledger — 2026-09-21

> Foundation mirror. This ledger is intentionally duplicated here so a future GitHub-only chat can reconstruct the engineering context from either repository.

> **Purpose:** durable project memory for future AI chats/agents. This document captures the engineering knowledge accumulated across the GitHub migration/scanning work: strategies, methods, test classes, logic invariants, security rules, workflow rules, failure lessons, and handoff requirements. It is intentionally broader than a normal source-of-truth file.

## 1. Canonical-state rule

Repository heads are deliberately **not treated as durable constants in this ledger**. A fresh chat must query `main` in both repositories before making changes.

Last verified implementation baselines at the start of this handoff:
- Foundation: `0e5e3532e91ea40040b718a8dcbf7e3f66919d30`
- Operations: `4a471024c2885c3167d1ec9b4b3c648b9e324e7e`

Since this ledger itself is a repository commit, the exact current head may advance without changing the engineering state described here.
- Foundation newer-scan hardening remains in PR #937 until protected checks pass.
- Operations #711 is the current concrete FIX_NOW defect discovered after the prior scan.
- Older runtime/control-plane acceptance issues remain evidence-gated and must not be "closed by assertion".
- GitHub and Cloudflare work are intentionally separated when connector limitations require separate chats.
- GitHub Actions is the canonical Foundation CI/CD and production deployment owner.
- Do not re-enable Cloudflare Workers Builds or Deploy Hooks.

## 2. Prime engineering principles

1. **Evidence outranks optimism.** Never call a feature production-complete from source inspection, a passing unit test, a dry-run, or a historical receipt when the acceptance requires live runtime evidence.
2. **One canonical authority per responsibility.** Avoid duplicate policy engines, identity engines, governance engines, replay authorities, or deployment authorities.
3. **Smallest stable responsibility first.** Migration is component decomposition, not wholesale rewrite.
4. **Preserve semantics before optimizing language.** Exact functional, security, policy, provenance, cancellation, timeout, resource-limit and error-taxonomy parity come before performance claims.
5. **Security must fail closed.** When a dependency/primitive is unavailable, use a safe failure rather than silently falling back to a weaker implementation.
6. **No fake production paths.** Test doubles are fine in tests, not in shipped production control paths.
7. **Current state must be self-describing.** Canonical docs should point to registries and current state, not become volatile historical release logs.
8. **Never hide blockers.** A multi-blocker workflow must preserve independent failure signals instead of stopping at the first failure.
9. **Do not create work merely to reduce issue count.** Older legitimate runtime evidence gates remain open until their evidence exists.

## 3. Four-lane / capacity-slot strategy

A "lane" means an execution capacity slot, not a permanent language assignment.

### Mandatory work-stealing rule
- No lane may remain idle.
- When a lane completes one language/component migration, immediately assign it the next compatible migration, scan, benchmark, differential corpus, adversarial test, documentation sync, or acceptance-evidence task.
- If one language has no more work, that lane changes language/component.
- Avoid duplicate work unless duplication is an intentional independent cross-check.
- Prefer four genuinely independent lanes with different starting/ending boundaries when the repository permits it.

### Lane allocation heuristics
- Split by stable responsibility, not file size alone.
- Separate policy-sensitive work from pure deterministic kernels.
- Separate security review from performance review when both are valuable.
- Serialize shared-contract edits through one owner to avoid contradictory changes.
- Parallelize independent corpora, language candidates, test families, and documentation reconciliation.

## 4. Full-project scanning strategy

A complete scan is not a single grep pass.

### Multi-language scan method
Use multiple paradigms to expose different classes of defects:
- Python: semantic/policy/control-flow correctness.
- TypeScript/JavaScript: browser, edge, adapter, frontend lifecycle and event/state contracts.
- Rust/Wasm: pure parser/normalization/security kernels, ownership and bounded-memory reasoning.
- Go: concurrency, fan-out, race, cancellation and resource-bound reasoning.
- JVM/.NET/C/C++/Zig/PHP: evaluate for specialized boundaries; do not force migration without a measured boundary.

### Every scan round should inspect
- bugs and defects;
- security flaws;
- policy/rules/logic inconsistencies;
- resource governance;
- retry/deadline/cancellation behavior;
- parsing/normalization semantics;
- provenance/lineage;
- replay/idempotency;
- persistence;
- deployment/CI;
- file placement and duplicate implementations;
- documentation and source-of-truth drift;
- test gaps;
- benchmark methodology;
- agent/model discoverability;
- portability across runtimes and tooling.

### Scan learning loop
1. Scan.
2. Classify findings by evidence tier: reproduced, code-read, tool/search hit, hypothesis.
3. Fix only reproducible/concrete issues first.
4. Convert surprising failures into new scan rules/tests.
5. Update the scan method itself.
6. Run another independent scan using a different language/paradigm.
7. Repeat until new scans predominantly rediscover known/retained authorities rather than new defects.

## 5. Migration ladder

Canonical sequence:

`inventory → reference → candidate → differential → shadow → authority candidate → canary → authority promoted → old authority retired`

### Authority-promotion requirements
- dependency readiness threshold;
- exact functional parity;
- security/policy/provenance parity;
- cancellation/timeout/error taxonomy parity;
- downstream coverage;
- repeated successful shadow passes;
- zero critical divergences;
- rollback path;
- recovery/incident rehearsal;
- runtime evidence;
- canary evidence;
- evidence grade appropriate to the responsibility.

### Critical architecture rule
Python remains the protected semantic/policy/persistence/replay/provenance/rollback authority until those promotion gates are actually satisfied.

## 6. Language-fit policy

### Python
Keep as authority for:
- policy/authorization;
- zero-cost/economic policy;
- resource/quota/lease governance;
- persistence/D1;
- replay/idempotency/terminalization;
- provenance/lineage;
- identity matching;
- promotion/adjudication/rollback;
- public Worker orchestration where no proven replacement boundary exists.

### TypeScript
Best-fit migration surfaces:
- browser lifecycle;
- edge routing;
- SSE/client lifecycle;
- frontend lifecycle;
- provider/search adapters;
- public endpoint discovery;
- Next.js/application state extraction;
- acquisition planner where the boundary is explicit.

### Rust/Wasm
Restrict to measured pure kernels:
- URL canonicalization;
- text normalization;
- generic HTML/product-card parsing;
- JSON/JSON-LD Product/ProductGroup parsing;
- Link-header parsing;
- robots/sitemap parsing;
- other deterministic bounded parser/normalization kernels.

Do not create a second identity/policy authority merely because Rust can reproduce the function.

### Go
Use when a justified concurrency/service boundary exists. Bounded HTTP fan-out is currently benchmark-complete but has no independently justified production service boundary.

### Java/Kotlin/.NET/C/C++/Zig/PHP
Remain deferred/specialized until a measured dependency, runtime or service boundary justifies them. A language with no candidate is explicitly dispositioned, not forgotten.

## 7. Differential testing standard

Whenever a migration candidate mirrors Python semantics:
- Python is the executable oracle.
- Freeze an orthogonal corpus.
- Generate candidate output in a machine-readable form.
- Compare exact normalized records, including failure states where applicable.
- Add adversarial/security cases.
- Repeat across multiple runs where relevant.
- Keep candidate and reference on the same Operations revision during Foundation CI.

### Required corpus properties
Cases should cover:
- happy paths;
- empty/null/falsy inputs;
- malformed syntax;
- boundary sizes;
- duplicates;
- ordering;
- case sensitivity;
- encoding;
- URL authority;
- default ports;
- fragments;
- userinfo;
- secret-bearing queries;
- redirects;
- cancellation/timeouts;
- partial output;
- resource limits;
- replay/idempotency;
- security-denied inputs.

32 cases is the minimum recurring corpus pattern for deterministic migration surfaces where applicable; use larger orthogonal sets when the contract warrants it.

## 8. Benchmark standard

Never report one timing number.

Where applicable collect:
- p50;
- p95;
- p99;
- throughput;
- CPU;
- wall time;
- allocations;
- memory;
- cold-start cost;
- serialization/deserialization cost;
- language-boundary conversion cost;
- resource cap behavior;
- concurrency/race behavior.

Benchmarks do not replace semantic differential tests.

## 9. Test taxonomy

Maintain multiple distinct test families:

### Unit
Small function/contract behavior.

### Differential
Candidate vs canonical Python/reference implementation.

### Metamorphic
Transformation should preserve or predictably alter output.

Examples:
- duplicate identical input remains deduplicated;
- harmless whitespace or fragment changes preserve canonical identity;
- query order remains preserved when Python preserves order;
- adding a forbidden credential must fail closed;
- changing method changes method-sensitive fingerprint.

### Malformed/security
- invalid URL;
- unsupported scheme;
- missing host;
- userinfo;
- unsafe/private/link-local/multicast/unspecified addresses;
- SSRF;
- DNS rebinding;
- oversized body;
- hostile regex input;
- secret query keys;
- cancellation/timeout/resource-limit paths.

### Determinism
Same input + same contract must produce same result and order.

### Race/concurrency
Especially for Go fan-out, reservations, idempotency/reclaim, and terminalization.

### Replay/idempotency
- duplicate requests;
- stale attempt identity;
- reclaim after lease expiry;
- terminalization races;
- restart;
- crash before acknowledgement;
- crash after external side effect.

### Persistence
- durable state across Worker/version boundaries;
- deletion/ownership/consent;
- quota/resource state;
- replay state.

### Runtime/live acceptance
Only close live issues on actual runtime/control-plane receipts.

## 10. Security rules learned

### SSRF
- Permit only `http`/`https`.
- Reject URL userinfo.
- Reject unsafe schemes.
- Resolve hostnames and require all resolved addresses to be public.
- Unwrap IPv4-mapped IPv6 addresses before classification.
- Require global/public IP semantics rather than relying only on private/reserved blocklists.
- Explicitly deny provider/platform-reserved addresses such as Azure `168.63.129.16`.
- Revalidate DNS immediately before connect and reject changed answers.
- Bound number of resolved addresses.
- Re-run policy after redirects.
- Do not trust a first DNS answer while the HTTP client resolves again later.

### Endpoint discovery
- Never synthesize hidden routes.
- Only detect explicit public references.
- Cap input bytes before decoding.
- Cap decoded characters.
- Bound regex gaps.
- Reject secret-bearing query keys.
- Reject credentials/userinfo.
- Compare origin using scheme + hostname + effective port.
- Keep deterministic dedupe by method + URL.
- Cap number of endpoints.

### Acquisition
- Stream large responses before applying response-size limits.
- Do not materialize arbitrarily large bodies before the cap.
- Preserve cancellation and timeout semantics.
- Preserve retry/error classifications.

### Credentials / signing
- Never reuse a bearer credential directly as a general-purpose HMAC key.
- Derive purpose-scoped keys with an explicit scope/version.
- Keep key derivation centralized.
- Protected task-envelope signing must remain fail-closed.

### Browser/security headers
Worker asset responses must enforce:
- CSP;
- `X-Frame-Options: DENY`;
- `Referrer-Policy: no-referrer`;
- `X-Content-Type-Options: nosniff`;
- narrow `connect-src` rather than broad `https:`.

### Logging
Do not expose:
- secrets;
- authorization tokens;
- unnecessary D1 identifiers;
- installation IDs or internal credentials;
- sensitive runtime configuration.

## 11. Error and failure semantics

### Provider error + settlement error
If both occur:
- never lose the original provider failure silently;
- preserve provider error context as a note/cause when settlement fails;
- surface the settlement failure as the governing error only when necessary;
- retain both causes for diagnostics.

### Production test doubles
No fake service/request implementation should silently become the fallback production behavior because a runtime dependency is unavailable. Fail explicitly.

### Failed run status
Never swallow failure to persist a terminal failed state:
- log the persistence error with run identifier;
- make stale-running repair/reaper behavior explicit.

## 12. Resource-governance invariants

Resource state must obey conservation laws:
- reserved units correspond exactly to active charged reservations;
- failed reservations cannot become charged;
- released reservations cannot subtract units they never charged;
- reconciliation must not create quota under-count;
- replay must not double-charge;
- idempotent reuse must distinguish same-identity replay from conflicting identity.

For #711, the key invariant is:

`SUM(amount WHERE state='reserved') == quota.reserved_units`

per applicable scope/window/kind, subject to the schema's explicit semantics.

## 13. Durable ledger transition rules

Treat reservation transitions as a closed state machine, not loose string updates.

A failed reservation must not reach `reserved` without proof of its own successful charge.

Prefer:
- charge;
- prove charge changed exactly one row;
- finalize from that proof;
- otherwise clean up;
- distinguish idempotent replay;
- distinguish identity mismatch;
- fail closed when SQL semantics are unsupported.

Fake D1 behavior must approximate real D1 transaction/autocommit semantics enough to avoid false failures.

## 14. Workflow / CI rules

- Explicit timeout on every runnable job.
- Explicit concurrency group on workflows with collision potential.
- Required checks must remain protected.
- Never bypass required checks to merge.
- Retry a failed check when transient failure is plausible.
- Inspect job logs before deciding a failure is unrelated.
- Use immutable action SHAs where the repository policy requires pinning.
- Use GitHub App token auth for private Operations reads.
- Foundation migration workflows dynamically resolve exactly one current Operations revision per run.
- Every Operations-consuming migration lane in a run must use that same immutable resolved SHA.
- Explicit manual SHA pins remain available for reproducible evidence.
- Keep Foundation-only jobs independent of Operations resolution.
- Preserve multi-blocker diagnostic stages; do not short-circuit after the first failure.

### Deployment authority
- GitHub Actions owns canonical production release.
- Do not enable Cloudflare Workers Builds.
- Do not add Deploy Hooks.
- Do not create a competing deployment workflow in Operations.

## 15. Documentation rules

### Source of truth
- Stable current-state docs describe architecture and ownership.
- They should not become volatile logs of every commit SHA.
- Historical dated records remain context only.
- Use dedicated registries/ledgers for migration state.

### Ownership
- Foundation owns public-safe common standards.
- Operations contains private/restricted addenda only.
- Do not fork the same public standard in both repos.
- One machine-readable registry should describe maintained polyglot candidates.

### Placement
- `polyglot/<capability>/` = canonical maintained multi-language candidate.
- `experiments/` = scratch/legacy/time-boxed only.
- `benchmark/polyglot/` = legacy/shared fixture harness; no new maintained candidate roots there.
- Registry must remain synchronized with implementation/corpus/evidence/disposition.

## 16. Issue-management strategy

### Separate implementation from acceptance
An issue can remain open even when repository code is complete if its acceptance requires live/runtime/control-plane evidence.

### Group similar issues only when
- same canonical owner;
- same authority/file surface;
- same acceptance condition.

Do not group distinct runtime gates merely to reduce issue count.

### Newer concrete defects
Fix concrete reproduced/code-read issues first.

### Older legitimate acceptance gates
Leave them open until:
- actual runtime receipt exists;
- deployment provenance is recorded;
- failure/rollback conditions are demonstrated as required.

### Issue labels
Use explicit labels such as:
- bug;
- security;
- maintenance;
- architecture;
- priority:high;
- needs:runtime-evidence;
- track:meta-tracker.

Keep issue body synchronized after merges and architecture changes.

## 17. Agent/AI execution strategy

- Prefer parallel independent agents/lanes.
- Use different languages/paradigms to expose different blind spots.
- Do not let all agents inspect the same starting file.
- Use different starting/ending boundaries.
- When a lane finishes, work-steal immediately.
- Feed lessons from one scan into the next scan strategy.
- Improve the agent instructions/registry/docs when recurring mistakes appear.
- Preserve reproducible commands and exact file/symbol ownership.
- Record why an approach was rejected, not only what was selected.
- Avoid model-specific assumptions; any coding model/agent should be able to discover the contract from repository docs.

## 18. Known failure lessons

1. A Go fan-out test initially used an ambiguous handler; use explicit typed handlers.
2. A TypeScript cancellation test initially expected TIMEOUT; actual contract was CANCELLED.
3. A Rust URL corpus once contained a credential-bearing case in a valid benchmark; credentials must be adversarial/fail-closed cases, not valid canonicalization benchmarks.
4. Rust robots corpus once used NaN/off-by-one expectations; use finite, normalized policy cases.
5. Migration workflow once used stale Operations SHAs; resolve the current Operations tip once per run.
6. GitHub App token flow needed client-id authorization for the private Operations repo.
7. Migration workflow artifact path and Python runtime version mismatches were real CI integration hazards.
8. WHATWG URL normalization can differ from Python semantics by lowercasing hosts/dropping explicit default ports; compare canonical authorities explicitly.
9. Python truthiness/default semantics differ from naïve TypeScript nullish logic.
10. JSON-LD falsy values can differ between languages; model Python truthiness deliberately.
11. Borrow/ownership issues can surface only after a semantic parity patch; compile-review the final Rust candidate, not only the test logic.
12. A benchmark existing does not mean a migration is complete.
13. A passing smoke path does not prove runtime acceptance.
14. A source-of-truth file that embeds stale SHAs becomes a source of confusion; prefer stable pointers + immutable baseline records.
15. Coverage percentages become misleading if high-value modules are omitted from the denominator.
16. A security test can be "green" while the production path still contains a fallback or duplicate implementation; trace the real consumer.
17. DNS validation before HTTP client connection is not sufficient if the HTTP client resolves again; revalidate at the connection boundary.
18. Quota/resource state must be modeled as a state machine with conservation invariants, not independent SQL updates.

## 19. Migration surfaces currently evidenced

### Rust
- URL identity/canonicalization;
- text normalization;
- active generic HTML/product extraction;
- JSON-LD Product/ProductGroup;
- Link-header pagination;
- robots/sitemap.

### TypeScript
- public endpoint discovery;
- Next.js/product state;
- search/provider adapters;
- browser acquisition;
- acquisition planner;
- public edge routing/SSE;
- frontend lifecycle.

### Go
- bounded HTTP fan-out.

### Intentionally retained authority
- policy;
- governance;
- persistence;
- replay/idempotency;
- provenance;
- identity;
- promotion/rollback;
- public Worker orchestration.

## 20. Runtime acceptance boundary

Repository-side evidence is complete for many migration candidates, but a candidate does not become production authority merely because:
- it compiles;
- it passes unit tests;
- it passes differential tests;
- it benchmarks faster.

Promotion requires:
- real deployment boundary;
- shadow receipt;
- canary;
- rollback rehearsal;
- downstream validation;
- production provenance.

## 21. Current concrete unfinished implementation work

### Operations #711
DurableResourceLedger orphan reservation defect:
- reproduce in a real checkout;
- implement proof-of-charge finalization;
- fix idempotent replay path;
- remove pending/illegal state deterministically;
- fix D1 fake transaction behavior;
- add quota-conservation regressions;
- validate real/preview D1 `changes()` semantics;
- run concurrent over-limit probe;
- retain acceptance evidence in the issue.

### Foundation #937
Final newer-scan hardening branch:
- run protected CI;
- fix any test failures;
- merge only after required checks are green;
- then synchronize main SHAs and issue bodies again.

## 22. New-chat startup checklist

Before changing code in a fresh chat:

1. Read this ledger.
2. Read `docs/GITHUB_CHAT_HANDOFF_2026-09-21.md`.
3. Read `docs/CURRENT_SOURCE_OF_TRUTH.md`.
4. Read `REPOSITORY_MAP.json`.
5. Inspect current Foundation/Operations main SHAs.
6. Inspect open PRs and the newest issues.
7. Treat #711 as the concrete implementation priority unless a newer blocker supersedes it.
8. Treat #937 as pending until protected checks prove otherwise.
9. Keep GitHub and Cloudflare work in their appropriate chats.
10. Do not duplicate authorities or reopen deliberately retained architecture.
11. Do not close runtime acceptance issues without their required runtime evidence.
12. Update this ledger when a new recurring strategy, rule, test class or failure lesson is discovered.

## 23. Definition of "nothing left behind"

A project learning is considered persisted only when it exists in at least one durable repository artifact:
- implementation;
- test/corpus;
- workflow/CI policy;
- registry;
- issue acceptance note;
- stable source-of-truth;
- migration ledger;
- or this continuity ledger.

If a future agent discovers a new strategy, invariant, test pattern, failure mode or policy that is not represented here, update this ledger before ending the work session.

## 24. Benchmark design beyond one corpus

When the project requests broad research/AI improvement benchmarks, vary more than the test inputs:
- topic/domain;
- approach/method;
- number of agents;
- serial vs parallel execution;
- model mix;
- tool mix;
- failure injection;
- corpus size;
- cold vs warm state;
- deterministic replay;
- adversarial/security condition.

The preferred research comparison set is often 30–40 scenarios rather than a tiny sample. Do not interpret a single benchmark configuration as representative of the whole system.

For migration candidates, use the smaller exact differential corpus pattern where contract identity matters, then layer benchmark diversity on top.

## 25. Research-source diversity strategy

For external research used to improve the project, diversify source types rather than trusting one community:
- GitHub/code/issues;
- Reddit/community discussions;
- YouTube/video demonstrations;
- public social discussion;
- documentation and standards;
- Chinese/community sources such as Baidu Tieba, Zhihu, Douban, PTT and Bilibili when technically relevant.

Source diversity is a research method, not evidence that all sources have equal reliability. Prefer primary documentation, reproducible code and direct evidence when sources conflict.

## 26. Zero-cost / cost-governance policy

The project has a strict zero-cost operating policy for the intended free-tier chatbot path.

Architecture principle:
- router tries the next eligible provider when one free quota is exhausted;
- no provider is treated as a sole point of free-tier availability;
- cost policy remains centralized in Operations;
- provider-specific adapters must not independently override zero-cost policy;
- runtime/provider selection must preserve resource reservations and budget accounting.

The intended routing family documented in project research includes Cloudflare Worker, Cloudflare Workers AI, Groq, Gemini Flash and GitHub/OpenRouter free model options. Exact quotas/prices are external mutable facts and must be re-verified before being used as current production assumptions.

## 27. Known Cloudflare/runtime configuration baseline

GitHub-side code must remain aligned with the separately owned runtime configuration:
- Operations Worker: `legacy private Worker`;
- public Foundation Worker: `legacy public Worker`;
- Operations D1 binding: canonical governance/memory database;
- production environment is explicit;
- `STRICT_ZERO_COST_ONLY=true`;
- governance cron is configured for a 15-minute interval;
- resource-governance scope/window/lease settings are explicit;
- governance policy JSON secrets are installed from the canonical policy;
- Workers Builds remain OFF;
- Deploy Hooks remain NONE.

Do not put credential values, private tokens or secret contents into GitHub documentation. Record only names, ownership and non-sensitive configuration semantics.

## 28. Runtime evidence handoff method

When a GitHub-only chat reaches a runtime acceptance gate:
1. record the exact requested receipt/field in the issue;
2. identify the owning runtime/deployment authority;
3. hand the task to the Cloudflare/runtime chat when connector separation requires it;
4. bring the resulting receipt back into GitHub issue/source-of-truth;
5. close only when the recorded acceptance field matches the documented closure rule.

Never replace this with a code-only assertion.

## 29. Newer post-scan concrete issues discovered after the main migration wave

These issues were created after the earlier #699 sweep and are part of the current handoff. They must not be lost merely because the older audit body predates them.

**Redacted from the public mirror (2026-09-27).** This section previously enumerated specific unresolved defect details for Operations issues #717–#721, including exploitable failure-mode specifics for a live authenticated service. That level of detail does not belong in a public repository regardless of the private repo's own security posture — it functions as a roadmap for anyone reading this file, not just future maintainers.

The issue numbers and one-line topics are kept here as pointers only; full defect detail, required acceptance criteria, and status live exclusively in the private Operations tracker (`operations` issue tracking, and cross-referenced from `operations#1103`).

- #717 — task-envelope/replay protection (private tracker for detail)
- #718 — Operations Worker/chat request-handling boundary (private tracker for detail)
- #719 — resource-ledger lifecycle (private tracker for detail; related to #711)
- #720 — protected policy enforcement/digest (private tracker for detail)
- #721 — SSE terminal-result vocabulary (private tracker for detail)

These newer issues are current implementation backlog; they are not the older live-runtime evidence gates. Do not restore the removed detail to this public mirror — if a future agent needs it, it belongs in `operations`.


---

# SOURCE: docs/AI_AGENT_HANDOFF.md

# 2026-09-24 LIVE HANDOFF OVERRIDE — CYCLE 7

Current family state: Foundation `2710b7559c9c7a0dcd2c84fe6ed77b8dbc684706`; Operations `1fd629cae593959249107ddb8c7af3f55292e9df`; 8 open issues; 1 open PR (#1137, documentation only); 0 open implementation PRs. Production Operations pin remains `fda24660843cacfe28de661cf170789af542d28f`; the latest successful production release ran at Foundation `725e1b9cdaa637f07d4264673cddfc8ab806b3c6`.

Latest runtime evidence: production release `36030977718` PASS; nightly research `36030996071` FAIL at upstream public Worker HTTP 403 / local `upstream_worker_rejected` 502; nightly canary `36030977932` FAIL at the same boundary. The remaining queue is evidence/runtime-gated.

Cloudflare control-plane reads were successfully verified during this audit: account membership 200 with [REDACTED-CF-ROLE]; Workers listing 200; D1 listing 200. Public/private Worker identities and the D1 database are present. Exact deployment-history/version freshness was not re-queried after the latest GitHub documentation commits, so do not promote an older deployment identifier to a new L4 receipt.

ChatGPT continuity: visible mobile/chat state is transport state, not execution authority. On unresponsiveness/context pressure, checkpoint to GitHub and resume in a fresh chat. App closure is an observed correlation only.

---

# 2026-09-24 CURRENT AUTHORITY RECONCILIATION — CYCLE 6

**Status:** LIVE — this header supersedes older dated authority/handoff sections below.

## Current family state
- Foundation main: `2710b7559c9c7a0dcd2c84fe6ed77b8dbc684706`
- Operations main: `ebf1e82734cb2fab0a8f4eddc8b1f342803740d1`
- Open issues: 8 total — Foundation #58/#157; Operations #145/#340/#385/#597/#603/#699.
- Open implementation PRs: 0 at the current checkpoint. Foundation documentation PR #1136 and Operations documentation PR #893 are merged.
- Current documentation reconciliation is in Foundation #1137 and Operations #894; Operations #894 is already merged, while Foundation #1137 is awaiting its required PR check.
- Canonical Operations production/nightly pin: `fda24660843cacfe28de661cf170789af542d28f`.

## Current runtime/evidence
- Canonical Foundation production release run `36030977718`: PASS against Operations `fda24660843cacfe28de661cf170789af542d28f`.
- Latest nightly research run `36030996071`: upstream public Worker HTTP 403, surfaced locally as HTTP 502 `upstream_worker_rejected`; this remains Foundation #157's provider/runtime blocker.
- Live nightly canary `36030977932`: same 403/502 boundary.
- These results do not authorize closing the remaining L4 evidence gates.

## Chat/session continuity
- The ChatGPT conversation became unresponsive and reached a practical context/length boundary. Treat the conversation as transport state, not as the execution ledger.
- Closing the Android app is an observed correlation only; do not infer that ordinary Chat-mode work either continued or stopped without authoritative receipts.
- External September 2026 research reviewed OpenAI Help/Status, OpenAI Community, Reddit, GitHub/Codex, mainstream technical coverage, Zhihu, Baidu Tieba, Douban, PTT and Bilibili. Strongest matching signals concern long-chat/mobile message-stream or synchronization instability; Chinese-language evidence was comparatively sparse/generic.
- Current operating rule: on responsiveness degradation, app closure during heavy work, or practical context/length pressure, stop expensive work, checkpoint in GitHub, and resume in a fresh chat.

## Authority boundary
Foundation owns public-safe core, GitHub Actions and canonical production deployment. Operations owns private runtime/control-plane behavior and must not become a competing GitHub Actions/deployment authority. Cloudflare L4 state requires a fresh Cloudflare control-plane receipt; no new standalone Cloudflare claim is inferred here.

---

# 2026-09-23 CURRENT AUTHORITY OVERRIDE

Current family state:
- Foundation main: `121ff5017c6b11ebc103dbbd26bdffe639fcc8cb`
- Operations main: `b47aa056f50d27df9b5f552495a6cd862ae8a697`
- Public Worker deployed provenance: `[REDACTED-PUBLIC-DEPLOYMENT-PROVENANCE]`
- Private Worker production provenance: `[REDACTED-OPERATIONS-PROVENANCE]`
- Nightly research Operations pin: `3a7e350ddd5648caf93f58651323425186544f66`
- Current open issue queue: Foundation #58/#157; Operations #145/#197/#340/#352/#385/#597/#603/#699/#711
- Open implementation PRs: 0
- Open PRs after the completed synchronization merges: 0
- Latest completed nightly research #861: blocked before provider execution; #862 is the next scheduled run and remains provider-gated
- Latest completed extractor benchmark #330: failed using stale Operations #830 (`246e563...`); corrected benchmark #333 is queued against `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`
- Coverage matrix #301: cancelled after the follow-up commit; corrected #302 is queued against `bfcfaf5941824559cc253ecb2fd7d517cb1f1d7f`
- Current deployed public Worker probe on `c465ed8cff860cf0f1a1d6de6655aaf9594f02d2`: PASS
- Full L4 runtime certification remains evidence-gated

Older dated checkpoints remain historical provenance only.

---
---
---

## 2026-09-22 FINAL LIVE REF RECONCILIATION

**Live branch heads queried from GitHub:**
- Foundation `main`: `f9490f36d7ffd877157f26d674b3bfc27388f67e`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

The live heads may contain documentation and migration-candidate commits after the verified runtime pins. Acceptance workflows intentionally remain pinned to the verified immutable revisions until promotion evidence passes.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Latest live branch heads queried from GitHub:**
- Foundation `main`: `86a7d02b86a78102bf412cdce050c1f9e6c95bd5`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Verified runtime implementation pins:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

**Important:** Operations `main` now contains merged migration-candidate/test fixes after the verified runtime pin. Those candidate revisions are not production/runtime certification and must not silently replace the immutable runtime pin in acceptance workflows. The coverage/runtime guard must fail closed when non-documentation drift exists after the approved pin.

## 2026-09-22 LIVE GITHUB REF RECONCILIATION

**Live branch heads observed immediately before this synchronization:**
- Foundation `main`: `baad1daf07ea7d0307077631c4afb3a27fa31e78`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`

**Last verified implementation revisions:**
- Foundation: `e5b26061861e570396b73993a3c8733496cb1956`
- Operations: `50e642dfb05846963a82fe76f4f5fe085d4b9a8c`

Documentation-only handoff commits may advance `main` without changing the verified runtime implementation revision. Always refresh live refs before mutation and keep live branch heads separate from runtime-certification pins.

## 2026-09-21 FINAL HANDOFF

Current heads:
- Foundation 985fd526913bdf48fffc73cfc7e834d38dd449de
- Operations 2da42873fa2ff7ae05df00973a7ba584cdd1c6a9

Completed in this work:
- rounds 5-6 scan findings reconciled;
- lifecycle/materialization fixes merged in Foundation #921;
- scan-method and maintenance documentation synchronized in Foundation #922 and Operations #670;
- Operations #650/#655/#656/#657 plus provider-configuration centralization #661 and deep-immutability residue #665 merged;
- issue labels and cross-issue relationships normalized;
- remaining queue reduced to explicit runtime/evidence acceptance gates.

The adaptive scan protocol is canonical in docs/CROSS_LANGUAGE_ADAPTIVE_SCAN_METHOD_2026-09-21.md and referenced by AGENTS.md.

---

## 2026-09-21 LIVE HANDOFF

Current GitHub heads:
- Foundation main: e50a84ee239937967f9c23412e94521d347e3466
- Operations main: 44c4dc2189efa9b5a6f0e5648f5c892c55b45746

Current implementation PR: Foundation #921 fixes #909/#910 with closed ResearchLifecycle semantics and bounded worker materialization.

Recently merged scan-derived Operations corrections: #650 Go fanout lifecycle/cancellation/deterministic receipt pilot; #655 ResourceLedgerSnapshot deep immutability; #656 explicit malformed provider-runtime diagnostics; #657 aggregate provider-stream output budget; #661 centralized provider configuration parsing; #665 nested-mutation hardening for frozen records.

Remaining queue is intentionally acceptance-driven; runtime-gated issues remain open until their live evidence exists.

Use AGENTS.md and docs/CROSS_LANGUAGE_ADAPTIVE_SCAN_METHOD_2026-09-21.md for all subsequent scan waves.

---

## 2026-09-20 VERIFIED HANDOFF

Start from Foundation `d4f8be98447d2b6c6d05d1b213941e029f8649a6` and Operations `dd30834aec8f1263d9b35142b1bd16b4ba95f1ca`.

Canonical production proof:
- Foundation production run `35519167159` / run number `321` = SUCCESS.
- Operations Cloudflare provenance = `github:[REDACTED-OPERATIONS-PROVENANCE]`.
- Operations active version observed by the release = `0dae35f1-854b-49e4-b278-f3a17af3aa00`.
- Runtime acceptance passed for chat, idempotency, SSE lifecycle, permitted-source research/readback, D1/B2, memory store/query/delete/owner boundary, replay guard, learning feedback, terminalization CAS, durable resource reservation/reconciliation, maintenance reconciliation and provider-stream contract.
- Cross-version memory/replay remains deferred.
- Live provider completion remains intentionally unavailable because no permitted provider is configured; deterministic fallback is explicit.

Migration:
- Foundation #862 is merged: exact pinned Foundation Git object/tree is asserted before public-core sync.
- Foundation #863 is the active follow-up correcting the pin discovery output contract; after it merges, run the fresh migration/extractor matrices before making candidate migration decisions.
- Do not treat earlier blob-mismatch failures as candidate failures; they were harness failures.
- Keep the 3 migration + 1 acceptance/blocker adaptive lane model.
## 2026-09-20 PRODUCTION PROMOTION OVERRIDE

- Foundation main before this promotion: 62ff421534034d70a110f1dba32f71975c7e5a2d.
- Operations main: 277ccb9ee33221038c7ca5647f19e27a00d84ea3.
- Production pin target: dd30834aec8f1263d9b35142b1bd16b4ba95f1ca (Operations #610, exact proven packaging fix).
- This is a deliberately immutable production target; it does not promote the newest Operations benchmark/docs commits.
- Fresh production certification is required after merge; historical production receipts do not certify this target.

## 2026-09-20 LIVE MIGRATION RECONCILIATION — CURRENT OVERRIDE

Refresh live GitHub refs before every mutation.

### Current repository heads
- Foundation main: 12cf25f6a5688522f945e48efed915a5d5902703.
- Operations main: b5982fd9c3203d360584f955b8adfcf85cfd1315.

### Active migration work
- Foundation #835 (TypeScript frontend controls) is merged.
- Foundation #836 is the documentation reconciliation PR.
- Operations #606, #607, #608, #609, #610 and #611 are merged.
- Operations #610 fixed the production Worker packaging defect where generated foundation_core was excluded from setuptools package discovery.
- Operations #603 remains the canonical AI-model/tooling portability tracker.
- Current main is not production-certified until a canonical production release proves the current revisions.

### Architecture invariant
Python remains protected policy/governance/persistence/provenance/replay/rollback authority. TypeScript/Rust/Go migration work remains evidence-gated. Operations remains free of GitHub Actions; Foundation remains the sole CI/CD/deployment owner.

# AI Agent Handoff — Research Intelligence Engine

## 2026-09-19 CURRENT HANDOFF — AUTHORITATIVE

This section is the continuity anchor for the next maintenance chat. Current GitHub state and fresh production evidence override all older sections in this file.

### Exact repository state

- Foundation `main`: `386dcad577cacf729ee49830548597ff5504de14`
- Operations `main`: `948d826851a7678fdf81a344aeaa21ad1f278e36`
- Foundation production Operations pin target: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation nightly research pin remains: `f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`
- Foundation PRs #739, #740, #741, #742, #808, #810, #811, #812, #814, #815, #816, #817 and #818 are merged.
- Operations PRs #535, #536, #537, #575, #576, #577, #578, #579, #581, #583, #584, #585, #586 and #587 are merged.
- Foundation #27 is closed.
- Operations contains no GitHub Actions workflow authority.

### Latest canonical production proof

Run `35456292033` (#232), Foundation `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`, last verified against Operations `f6600c068de6e17af1e0e99c1f3ba4b0f06f31b5`. The next production certification target is Operations `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`.

The release verified:

- public Worker deployment/readiness;
- private Operations Worker deployment and Cloudflare provenance `github:[REDACTED-OPERATIONS-PROVENANCE]`;
- authenticated chat and idempotent replay;
- authenticated SSE lifecycle;
- permitted-source research ingestion/readback;
- D1/B2 lifecycle;
- memory store/query/delete and owner boundary;
- durable task-envelope replay protection;
- candidate learning and rating-feedback candidate flow;
- durable terminalization CAS;
- durable resource reserve/consume and reconciliation;
- maintenance scheduler reconciliation;
- provider-stream contract.

The production release emitted and uploaded `cross-repository-audit-receipt`. The release itself completed successfully.

### Repository-side fixes completed in this sequence

- Operations #535: family audit excludes approved compatibility facades.
- Operations #536: nested `foundation_core.*` compatibility facades are recognized correctly.
- Operations #537: terminalization CAS requires the current durable attempt identity and prevents stale/reclaimed attempts from masquerading as valid duplicate terminalization.
- Foundation #741: pins the corrected nested-facade audit revision.
- Foundation #742: pins the corrected terminalization runtime revision.
- Production run `35456292033` exercised the merged Operations terminalization correction successfully.

### Remaining queue

Foundation:
- #157 — real 24-program nightly execution/artifact evidence remains missing because the current push-triggered nightly run still fails before job creation.
- #263 — repository-side bridge v3 is fixed and merged; one real workflow-dispatch receipt with exact target SHA and actual job creation remains missing.
- #452 — repository SSE lifecycle is green; current architecture uses non-streaming provider calls, so remaining proof is real client cancellation/disconnect propagation; a true provider-error-after-partial-output path would require a separate incremental-provider-streaming feature.
- #58 — meta tracker remains open until the dependent gates above are genuinely satisfied.

Operations:
- #119 — live memory persistence across restart plus endpoint authorization/deletion.
- #120 — live durable feedback retention plus evaluation/benchmark integration.
- #132 — live replay-guard persistence/rejection across an actual restart/instance boundary.
- #145 — external approved scheduler activation.
- #155 — current cross-repository audit receipt is green in production; supported bridge-dispatch evidence is still required.
- #197 — broader approved runtime conversational acceptance.
- #340 — deeper provider streaming interruption/cancellation/error evidence.
- #352 — representative API/feed/HTML/browser extractor/mapper replay matrix with failures/retries/restarts/idempotency/provenance.
- #385 — broader concurrent completion/failure/cancellation, crash-after-side-effect, late-output, and restart/recovery acceptance. Unexpected chat exceptions are durable `failed` terminal receipts via #579, and unresolved external intents fail closed via #585; remaining broader recovery/runtime gates are still open.

### Do not regress the architecture

- Foundation remains the only GitHub Actions and canonical production deployment owner.
- Operations remains private and contains no GitHub Actions workflows.
- Do not add Cloudflare Workers Builds or Deploy Hooks.
- Do not create a second memory store, resource ledger, replay authority, lifecycle authority, evaluator, publication authority, or deployment path.
- Do not close runtime/external issues from source inspection or unit tests alone.

### Queue continuation

Use `FIX_NOW | INTEGRATE | VERIFY_REPO | RUNTIME_GATE | EXTERNAL_BLOCKED | DUPLICATE | SUPERSEDED | ROADMAP`.

For every mutation, preserve:
`issue -> canonical owner -> revision -> acceptance rung -> checks -> PR -> missing evidence`.

When a queue item is RUNTIME_GATE or EXTERNAL_BLOCKED, record the exact missing evidence on the issue and move to the next independent lane. The current repository migration sequence is TS edge/search/browser -> Rust measured kernels -> optional Go sidecars, while Python remains the protected rollback/policy authority.

