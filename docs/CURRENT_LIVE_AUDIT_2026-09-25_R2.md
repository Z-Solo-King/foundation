# 2026-09-25 CURRENT LIVE AUDIT R2

This is the compact authoritative cross-surface checkpoint for the 2026-09-25 re-audit. Fresh GitHub/Cloudflare reads outrank older dated documents. This file is documentation-only; its commit may advance `main` beyond the audited code heads below.

## GitHub
- Audited Foundation code head: `dbab61bb15aae22ca19787ddc70283af2617620e`.
- Audited Operations code head: `300bb0cf8dc8f8a3a874c2bbeadc7ee5ddc6eb8c`.
- Open issues: **11** — Foundation #58, #1157, #157; Operations #145, #197, #340, #385, #597, #603, #699, #713.
- Open PRs at audit start: **3** — Foundation #1203 (documentation-only, stale base, latest Public tests + Six-lane exhaustive audit checks failing); Operations #914/#915 (Dependabot development dependencies, no Actions checks recorded).
- Open implementation PRs: **0**.
- Current repository defect: Operations #713 remains open. Fresh CI run `36119832079` reproduced corpus `u47` differential mismatch: Python accepted `http://64:ff9b::127.0.0.1/`, Rust rejected it. Subsequent NAT64/corpus-registration fixes are on current main, but a fresh post-fix differential receipt is still required.
- Last known clean family-integrity receipt: run `36119501613` PASS; current heads have advanced since that receipt.

## Cloudflare
- Account membership/control-plane: **HTTP 200**, role **Super Administrator - All Privileges**.
- Worker listing: **HTTP 200**; canonical public `foundation`, canonical private `operations`.
- Current deployed Foundation version: `93aa2e4e-cf67-41de-9933-95f8822de423`, provenance `github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c`.
- Current deployed Operations version: `66e335b9-68da-429b-abcf-29f9c7e2f5ac`, provenance `github:a3171f353539f1a31020c432f98cf0530cbf91ef`.
- Current GitHub code heads are newer than those deployed production revisions; they are not yet production-certified/deployed.
- `heroic-ai.dev`: **pending / unresolvable**. Production release, preflight and public Worker probes fail at this public-domain DNS/zone boundary.
- Assigned nameservers: `abdullah.ns.cloudflare.com`, `tricia.ns.cloudflare.com`. Root Worker-managed proxied AAAA is `100::`; no manual Worker routes are present.
- D1 `research-intelligence`: **HTTP 200**, ID `19f51638-47a5-4218-a9dc-73dbfd6156fe`. Direct `sqlite_master` inspection finds 21 tables.
- Live D1 row counts: research_runs 644; observations 398; research_publications 0; resource_governance_reservations 422; resource_governance_quota 110; chat_idempotency 1278; chat_memory_records 3; chat_learning_observations 0.
- Operations Worker configuration observed: Workers AI `@cf/zai-org/glm-4.7-flash`, fallback `@cf/google/gemma-4-26b-a4b-it`, `STRICT_ZERO_COST_ONLY=true`, schedule `*/15 * * * *`. Secret values were not read or exposed.

## Nightly research
- Active run `36141145555`: waiting at the exact production-release gate; deterministic polyglot migration review completed, provider-backed lanes have not started.
- Production gate `36141127503`: **FAIL** after 1040 repository tests and Cloudflare account/D1 authorization checks passed; failure is the inactive/unresolvable `heroic-ai.dev` zone.
- Provider preflight `36141127495`: **FAIL CLOSED**. Research endpoint/model/API-key presence checks are true; public Worker health and Worker-backed Workers AI probes are HTTP 000, curl exit 6, `dns_or_network_unreachable`, `Could not resolve host: Heroic-Ai.dev`.
- Public Worker probe `36141127548`: **FAIL** at the same public DNS boundary.
- No provider-backed 24-program acceptance receipt is certified.
- Latest nightly migration-review artifact: `10866905405`, digest `sha256:37a8daaf0c8890e449c534fcc5c0b85c70704784a54b3d30bfacb781e75cb6e0`. Score 60.0/100; 40 language/matrix rows; 24/24 capacity cases; 24 findings; 6 high findings; 890 migration candidates; 1,394 source files; 157,567 source lines; deterministic-structural evidence only; runtime performance validity false.

## Latest completed extractor benchmark
- Run `36119832050`, run number 447, completed successfully with **30/30 jobs successful**.
- Aggregate artifact: **`10857765019`** (`live-extractor-benchmark-40way`), digest `sha256:c110306bffb021b51ffd304562f25bd77d010aadd81fa538871cfad7ab772544`.
- 40 receipts: API 12 / browser 8 / feed 8 / HTML 12; 4 ok / 32 empty / 4 blocked.
- Completion rate 0.10; error rate 0.0; invalid resource rows 0; missing key rows 0; provenance completeness 1.0; route provenance completeness 1.0; repeat reliability 1.0; unstable repeated groups 0; recovery rate 1.0.
- Evidence boundary: this benchmark ran against Foundation head `e6514890548278e26331269e4abb0818b119233a`, before the later `dbab61bb` NAT64/hybrid repair. It is the latest completed benchmark, but not current-main validation.

## PR/issue disposition
- Foundation #1203 is a stale documentation PR; the R2 checkpoint supersedes it.
- Operations #914/#915 are dependency PRs without Actions receipts; do not merge solely from metadata.
- Operations #713 is the only newly reproduced repository-level correctness defect in the current open queue. The other open items are runtime/evidence/migration acceptance gates under their issue contracts.

## ChatGPT continuity
- ChatGPT/mobile UI is transport state only. GitHub commits, workflow/artifact receipts, and Cloudflare control-plane/runtime receipts are authoritative.
- Preserve `issue -> owner -> audited revision -> evidence tier -> run/artifact -> blocker -> next action`.
- Do not close runtime/production gates from source inspection or deterministic CI alone.
- Do not add a competing Cloudflare deployment authority or alternate public hostname to bypass `heroic-ai.dev`.

## Audit status
**Repository access:** working. **Cloudflare control-plane access:** working. **Repository/production synchronization:** intentionally separated by immutable production pins, but current main is not deployed. **Production:** blocked by domain/zone activation. **Nightly provider execution:** blocked by the same public Worker/DNS boundary. **Benchmark:** completed strict-integrity pass, but not current-main validated. **Current code defect:** #713 remains open pending fresh differential parity evidence.
