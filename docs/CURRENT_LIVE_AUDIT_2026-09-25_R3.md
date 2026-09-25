# 2026-09-25 CURRENT LIVE AUDIT R3

This is the latest compact cross-surface checkpoint. Fresh live GitHub/Cloudflare receipts outrank older dated sections.

## GitHub
- Foundation code head: `dbab61bb15aae22ca19787ddc70283af2617620e`.
- Operations code head: `cc4d885f09d2275192631ce56ba3429a4c3396a9`.
- Open issues: **11** — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699/#713.
- Open PRs: **3** — Foundation #1206 (live-state reconciliation, currently being refreshed); Operations #914/#915 (Dependabot development dependencies). **0 implementation PRs**.
- Foundation branch protection is working: direct main writes require the required status checks/PR path.
- #713 remains OPEN because its original live differential run `36119832079` reproduced a Python/Rust NAT64 URL-parity mismatch; current NAT64/corpus/test repairs are merged, but a fresh post-fix differential receipt is still required.

## Cloudflare
- Control-plane access: working; account membership HTTP 200; role **Super Administrator - All Privileges**.
- Canonical Workers: public `foundation`, private `operations`.
- Deployed Foundation version `93aa2e4e-cf67-41de-9933-95f8822de423`, provenance `github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c`.
- Deployed Operations version `66e335b9-68da-429b-abcf-29f9c7e2f5ac`, provenance `github:a3171f353539f1a31020c432f98cf0530cbf91ef`.
- Current GitHub code heads are newer than the deployed production pair; they are not production-certified/deployed.
- Zone `heroic-ai.dev`: **pending / unresolvable**. Assigned nameservers: `abdullah.ns.cloudflare.com`, `tricia.ns.cloudflare.com`. Worker-managed root AAAA `100::` is present; manual Worker routes are absent.
- D1 `research-intelligence`: HTTP 200; ID `19f51638-47a5-4218-a9dc-73dbfd6156fe`; direct `sqlite_master` query exposes 21 tables.
- Live D1 counts: research_runs 644; observations 398; research_publications 0; resource_governance_reservations 422; resource_governance_quota 110; chat_idempotency 1278; chat_memory_records 3; chat_learning_observations 0.
- Operations runtime config: Workers AI `@cf/zai-org/glm-4.7-flash`, fallback `@cf/google/gemma-4-26b-a4b-it`, `STRICT_ZERO_COST_ONLY=true`, cron `*/15 * * * *`. Secret values were not exposed.

## Nightly research
- Active run `36141145555` is now **blocked_before_execution**. The exact production-release gate failed, the three live research lanes were cancelled, and the diagnosis job completed.
- Production run `36141127503`: **FAIL** after 1040 repository tests and Cloudflare account/D1 authorization passed; failure was the inactive/unresolvable `heroic-ai.dev` zone.
- Provider preflight `36141127495`: **FAIL CLOSED** — research endpoint/API key/model presence true, but public Worker health and Worker-backed Workers AI probes were HTTP 000, curl 6, `dns_or_network_unreachable`, host resolution failure.
- Public Worker probe `36141127548`: **FAIL** at the same DNS boundary.
- Nightly diagnosis artifact `10868805522`, digest `sha256:9ad02dc60b296e402c5450a6c06a70c25fb2441cb5c60bc8a299405d805ecd67`.
- No provider-backed 24-program acceptance receipt exists. No real-research findings are authorized from this blocked run.

## Latest completed extractor benchmark
- Latest completed benchmark: **#448 / run `36141127492`**, executed on Foundation `dbab61bb15aae22ca19787ddc70283af2617620e` with Operations ref `a3171f353539f1a31020c432f98cf0530cbf91ef`.
- Aggregate artifact `10867020802`, `live-extractor-benchmark-40way`, digest `sha256:073ad2ba3df5bad3f9536abe95281ec596e109d7293b4bc4d30499e11cb21e62`.
- Direct artifact inspection: 40 receipts; API 12 / browser 8 / feed 8 / HTML 12; 4 ok / 32 empty / 4 blocked; completion rate 0.10; error rate 0; invalid resource rows 0; missing key rows 0; provenance completeness 1.0; route provenance 1.0; repeat reliability 1.0; unstable groups 0; recovery rate 1.0; all 30 benchmark jobs succeeded.
- This is a **structural integrity pass**, not 40 successful business-data acquisitions. The 32 empty results remain observations, and the 4 ok results do not establish field-level correctness.

## Nightly migration review
- Artifact `10866905405`, digest `sha256:37a8daaf0c8890e449c534fcc5c0b85c70704784a54b3d30bfacb781e75cb6e0`.
- Review score 60.0/100; 40 language/matrix rows; 24/24 capacity cases; 24 findings, 6 high-severity; 890 migration candidates; 1,394 source files; 157,567 source lines.
- Evidence class is deterministic-structural; runtime-performance validity is false.

## Authority / ChatGPT
- GitHub commits, Actions/artifacts and Cloudflare control-plane/runtime receipts are authoritative; ChatGPT/mobile UI is transport state only.
- Keep production pins and deployed provenance separate from live `main`.
- Preserve `issue -> owner -> revision -> evidence tier -> run/artifact -> blocker -> next action`.
- Runtime/production gates stay open until their required live receipt exists. Do not add a competing Cloudflare deployment authority or alternate public hostname.
