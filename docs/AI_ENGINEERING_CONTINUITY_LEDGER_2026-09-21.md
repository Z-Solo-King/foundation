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

### #717 — task-envelope/replay protection
Concrete issues:
- in-memory replay guard can evict a still-live nonce under capacity pressure;
- missing `OPERATIONS_DB` can silently downgrade production replay protection;
- per-request DDL/purge costs governance budget;
- injected verification clock is ignored by signing/validation path;
- non-ASCII `compare_digest` inputs can raise `TypeError`;
- broad D1 error-message matching can misclassify operational failures as replay.

Required acceptance:
- live nonce cannot be re-admitted;
- production missing-DB path fails closed;
- injected-clock verification is deterministic;
- non-ASCII auth/signatures become stable auth failures;
- D1 replay classification is precise;
- measure replay-guard D1 statements.

### #718 — Operations Worker/chat boundary
Concrete issues:
- authenticate before parsing oversized request bodies;
- cap request bytes before materialization;
- do not return raw exception text;
- map authorization failures consistently to 401/403;
- reject string `requested_fields` instead of coercing into characters;
- record external-provider intent even when generation fails;
- remove the stray pytest function from production `chat_endpoint.py`;
- use exact segment-aware route matching and correct 405 behavior;
- split `handle_chat` into testable stages.

### #719 — resource-ledger lifecycle
Concrete issues:
- poison expired rows must not stop reconciliation of later rows;
- preserve partial progress and failed-row reporting;
- deadline expiry immediately after reservation must release the reservation;
- settlement cancellation must not leave resource state unsettled;
- enumerate every ResourceKind and its actual reservation call site;
- add reservation/quota conservation invariant probes.

Related to #711. Land the reservation orphan fix before broad ledger lifecycle refactoring.

### #720 — protected policy enforcement/digest
Concrete issues:
- `assert_protected(..., False)` is a no-op at current call sites and should not masquerade as an authorization gate;
- policy digest currently fingerprints policy names rather than semantic gating rules;
- verify actual digest callers before deciding whether to integrate or remove;
- acceptance requires a real protected-mutation rejection test or an explicit traceability correction.

### #721 — SSE terminal-result vocabulary
Concrete issues:
- `NOT_ATTEMPTED` currently degrades to stream status `failed`;
- unknown future states also silently become failed;
- use one closed terminal-outcome vocabulary across chat endpoint and streaming;
- map `NOT_ATTEMPTED` explicitly;
- reject unknown states through the existing contract-violation path;
- retain the event-loop cancellation yield between events.

These newer issues are current implementation backlog; they are not the older live-runtime evidence gates.

