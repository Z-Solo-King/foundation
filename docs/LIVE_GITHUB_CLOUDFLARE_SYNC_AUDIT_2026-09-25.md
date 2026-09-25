# 2026-09-25 CURRENT LIVE SNAPSHOT

This section is authoritative for this audit cycle. Fresh GitHub/Cloudflare reads and workflow/artifact receipts outrank historical sections below.

## GitHub
- Foundation main code baseline: dbab61bb15aae22ca19787ddc70283af2617620e
- Operations main code baseline: 7d77056cbdd72fae4c3bc73ab9a980f8a888a64e
- Open issues: 11 total — Foundation #58/#157/#1157; Operations #145/#197/#340/#385/#597/#603/#699/#713.
- Open PRs: Operations #914/#915. No Foundation implementation PR remains open; superseded docs PRs #1203/#1205 are closed.
- #713 remains open pending a fresh hybrid differential receipt on the current cross-repo pins.

## Cloudflare
- Canonical Workers: foundation and operations. Legacy research-intelligence-engine workers remain present.
- Current deployed provenance is intentionally separate from GitHub main:
  - foundation: github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c
  - operations: github:a3171f353539f1a31020c432f98cf0530cbf91ef
- heroic-ai.dev zone status: pending; activation failure reason: unresolvable.
- Public DNS resolution fails; production release and provider preflight stop at this boundary.
- D1 research-intelligence id 19f51638-47a5-4218-a9dc-73dbfd6156fe is queryable; direct schema is populated despite stale control-plane num_tables metadata.

## Nightly research
- Current nightly run: 36141145555 (#375), gated by exact production release.
- Production release #587: 36141127503 failed at heroic-ai.dev zone prerequisite.
- Provider preflight #158: 36141127495 failed closed with HTTP 000 / curl 6 / dns_or_network_unreachable.
- Public probe #158: 36141127548 failed at the same DNS boundary.
- No provider-backed 24-program acceptance receipt is certified.
- D1 live counts observed: 442 completed research runs, 202 planned, 398 observations, 0 publications, 0 stuck resource reservations, 422 resource-governance quota rows, 110 chat-idempotency rows.

## Latest extractor benchmark
- Benchmark #448: run 36141127492, completed successfully on Foundation dbab61bb.
- Aggregate artifact 10867020802; SHA-256 sha256:073ad2ba3df5bad3f9536abe95281ec596e109d7293b4bc4d30499e11cb21e62.
- 40 receipts: API 12 / browser 8 / feed 8 / HTML 12.
- Structural contract: pass=true; 4 ok / 32 empty / 4 blocked; completion_rate 0.1; error_rate 0; invalid rows 0; missing key rows 0; provenance and route provenance 1.0; repeat reliability 1.0; unstable groups 0.
- This is not 40 successful business-data acquisitions. The 4 ok receipts are synthetic listing-level placeholders without price/brand/spec/image/offer completeness; Fake Store API cases were blocked with 403.

## Audit fixes already merged
- Foundation #1204 -> dbab61bb: NAT64 URL safety and hybrid ref-output regression.
- Operations #953 -> 4c6432a8: NAT64/private destination hardening + negative corpus.
- Operations #954 -> b0c8503a: live issue inventory reconciliation.
- Operations #955 -> 7f471efc: Foundation public-core pin update.
- Operations #956 -> 300bb0cf: audit matrix reconciliation.
- Operations #958 -> b7a19d9: canonical OPEN_ISSUE_SCAN_RULES registration for #713.

## ChatGPT continuity
- GitHub commits, workflow receipts/artifacts and Cloudflare runtime/control-plane reads are authoritative.
- Keep branch heads, immutable production pins and deployed Worker provenance separate.
- Do not close runtime/L4 issues from deterministic CI alone.
- Do not claim DNS or production closure without active zone/public resolution.
- Authenticated numeric GitHub rate-limit allowance is not exposed by the connected fetch surface.

# 2026-09-25 POST-MERGE LIVE AUDIT OVERRIDE

This is the current post-merge source-of-truth snapshot.

- Foundation main: e6514890548278e26331269e4abb0818b119233a
- Operations main: add667236a17f2b845a39ae539f3dfe137d806a2
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs: 2 — Operations #914/#915 (Dependabot development dependencies). Foundation has none. No project implementation PR remains open.
- Repository fixes merged in this cycle: Foundation #1194, #1196, #1197, #1198, #1199, #1200, #1201, plus documentation #1195.
- Latest clean family-integrity run on corrected main: 36119501613 PASS.
- Latest production run 36119501519: FAIL only at Cloudflare zone activation prerequisite after 1040 repository tests and Cloudflare account/D1 authorization checks passed.
- Latest provider preflight 36119501717: FAIL CLOSED on DNS — HTTP 000, curl exit 6, dns_or_network_unreachable.
- Latest public Worker live probe 36119501481: FAIL at the same public-domain DNS boundary.
- Latest completed extractor benchmark remains run 36118106992, artifact 10855896489, digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d; 40 receipts, 4 ok / 32 empty / 4 blocked, provenance 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable groups, 0 invalid resource rows, 0 missing key rows.
- Active nightly run 36119514469 remains behind the exact production gate; no provider-backed 24-program acceptance receipt is certified.
- Cloudflare account role: Super Administrator - All Privileges. Zone heroic-ai.dev remains pending/unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance github:a3171f353539f1a31020c432f98cf0530cbf91ef.
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

Current verified cross-surface snapshot. Live workflow receipts and Cloudflare control-plane state outrank older dated sections.

- Foundation main: f7f824fde15e66d6ec6b4c9065feed124a1ce78d
- Operations main: 24ad53750ecf95084a468ebdb91dc6a3f34ab466
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs at audit snapshot: Foundation #1195 (this documentation reconciliation); Operations #914/#915 (Dependabot). No implementation PR remains open.
- Merged repairs in this cycle: #1194 Cloudflare release authentication header; #1196 nightly preflight network diagnostics; #1197 dual GitHub-token family scan; #1198/#1199 family issue-key normalization; #1200 truthful cancelled-lane nightly fan-in; #1201 canonical nightly workflow structure.
- Family integrity on corrected main: run 36119000013 PASS.
- Production run 36119000062 FAIL: 1040 repository tests and Cloudflare account/D1 authorization checks pass; release stops only because heroic-ai.dev is not an active Cloudflare zone.
- Provider preflight 36118999990 FAIL CLOSED: HTTP 000, curl exit 6, dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev.
- Latest completed extractor benchmark: run 36118106992; artifact 10855896489; digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d; 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; 0 unstable groups; 0 invalid resource rows; 0 missing key rows.
- Current nightly run 36119013418 remains behind its exact production gate; no provider-backed 24-program acceptance receipt is certified.
- Cloudflare account: Super Administrator - All Privileges; heroic-ai.dev pending/unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance github:a3171f353539f1a31020c432f98cf0530cbf91ef; D1 research-intelligence ID 19f51638-47a5-4218-a9dc-73dbfd6156fe.
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare runtime receipts are authoritative.
- No runtime or production issue is considered closed without its required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub/Cloudflare evidence outranks older checkpoint values below.

- Foundation main: 6b43bafa0f1d298e9a1a2c84b6721bb1eea4d0ac
- Operations main: b370dc959171dbfb35eae42c2acdee827917ee3f
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: Foundation #1195; Operations #914/#915. No implementation PR remains open.
- Repository fixes merged this cycle: #1194 (Cloudflare release auth), #1196 (nightly preflight diagnostics), #1197 (dual family tokens), #1198/#1199 (family issue-key normalization), #1200 (truthful nightly fan-in for cancelled lanes).
- Current production release 36118107525: FAIL at the Cloudflare zone prerequisite after repository and Cloudflare account/D1 authorization checks passed. heroic-ai.dev is not an active Cloudflare zone in the configured account.
- Current preflight 36118107000: FAIL closed with HTTP 000, curl exit 6, dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev; no diagnostic parser crash.
- Current family integrity 36118107049: PASS after the final family normalization repair.
- Newest completed live extractor benchmark: run 36118106992 on Foundation 70093db3; artifact 10855896489; digest sha256:8b37d570f60d0cf44a6353e23955a945e69c45b54db59b25f9e402789d72f37d. Direct artifact inspection confirms pass=true, 40 receipts, 0 invalid resource rows, 0 missing key rows, provenance completeness 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable repeated groups, status 4 ok / 32 empty / 4 blocked, recovery rate 1.0.
- Latest nightly multi-agent cycle is correctly gated before provider execution because production is not certified; there is no new provider-backed 24-program acceptance receipt from this environment.
- Cloudflare account role: Super Administrator - All Privileges. Zone heroic-ai.dev remains pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance remains github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance remains github:a3171f353539f1a31020c432f98cf0530cbf91ef; D1 research-intelligence ID 19f51638-47a5-4218-a9dc-73dbfd6156fe.
- Canonical Worker subdomains are disabled; do not create a competing public authority to bypass the requested heroic-ai.dev domain.
- ChatGPT/UI state is transport state only; GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.
- No runtime or production issue is closed without the required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub and Cloudflare evidence outrank older checkpoint values below.

- Foundation main: 70093db359570b3f87d135e26b525645135fa517
- Operations main: b370dc959171dbfb35eae42c2acdee827917ee3f
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: 3 — Foundation #1195 (this documentation reconciliation); Operations #914/#915 (Dependabot development-dependency updates). No implementation PR remains open.
- Foundation PRs #1194, #1196, #1197, #1198, #1199 fixed confirmed Cloudflare-release/family-integrity/preflight defects and are merged.
- Current production release 36118107525: FAIL at the Cloudflare zone prerequisite after repository and Cloudflare account/D1 authorization checks passed. heroic-ai.dev is not an active zone in the configured account.
- Current provider preflight 36118107000: FAIL closed with truthful transport evidence — HTTP 000, curl exit 6, network_classification dns_or_network_unreachable, Could not resolve host: Heroic-Ai.dev. No parser crash.
- Current family integrity 36118107049: PASS.
- Latest completed extractor benchmark 36115560009: PASS; artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e; 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; unstable repeated groups 0.
- The newer current-main extractor benchmark (36118106992) has not yet produced a completed replacement artifact; retain 36115560009 as the latest completed benchmark.
- Cloudflare account role: Super Administrator - All Privileges. Zone heroic-ai.dev remains pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance is github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance is github:a3171f353539f1a31020c432f98cf0530cbf91ef; D1 research-intelligence ID is 19f51638-47a5-4218-a9dc-73dbfd6156fe.
- Nightly multi-agent research is correctly blocked behind the exact production gate; no provider-backed 24-program receipt is certified.
- ChatGPT/UI state is transport state only; GitHub workflow/artifact receipts and Cloudflare control-plane/runtime evidence are authoritative.
- No runtime or production issue is closed without its required live receipt.

---

# 2026-09-25 FINAL LIVE AUDIT OVERRIDE

This section is the current cross-surface continuation point. Live GitHub and Cloudflare evidence overrides older checkpoint values below.

- Foundation main: 6eb531095148cb6657bccc72a64542691dbb6fa1
- Operations main: 207d8a3f081f58702b56fe64c57fe2c3042ce75d
- Open issues: 10 — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open project PRs: Foundation #1195; Operations #914/#915. Older duplicate implementation/documentation PRs #1186/#1187/#951 are closed as superseded.
- Production release 36117585242 is the current fresh run; the prior current-head run was blocked because heroic-ai.dev is not an active Cloudflare zone.
- Provider preflight 36117585207 is the current fresh run; the immediately prior corrected preflight recorded HTTP 000 / curl exit 6 / DNS resolution failure without crashing.
- Family integrity 36117585223 is the current fresh run after the dual-token fix; the previous failure was traced to using a private Operations-only token for the Foundation public issue inventory.
- Latest completed extractor benchmark 36115560009 passed the strict integrity gate: 40 receipts; 4 ok / 32 empty / 4 blocked; provenance 1.0; route provenance 1.0; repeat reliability 1.0; 0 unstable groups. Artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e.
- Cloudflare account access: Super Administrator - All Privileges. Zone heroic-ai.dev is pending/unresolvable; custom domain is enabled on foundation; deployed Foundation provenance github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance github:a3171f353539f1a31020c432f98cf0530cbf91ef; D1 research-intelligence ID 19f51638-47a5-4218-a9dc-73dbfd6156fe.
- ChatGPT/UI state is transport state only. GitHub workflow/artifact receipts and Cloudflare runtime receipts are authoritative.
- No runtime/production closure is asserted without the required live receipt.

---

# 2026-09-25 CURRENT LIVE AUDIT OVERRIDE

This section supersedes older dated checkpoint values for current-state interpretation. GitHub live refs and Cloudflare runtime receipts are authoritative.

- Foundation main at this audit snapshot: 01bfa0c6a74bf6f10082ac8034aa1b2d098d0e42.
- Operations main at this audit snapshot: 207d8a3f081f58702b56fe64c57fe2c3042ce75d.
- Open issues: 10 total — Foundation #58/#1157/#157; Operations #145/#197/#340/#385/#597/#603/#699.
- Open PRs after duplicate cleanup: Foundation #1194; Operations #914/#915. Foundation #1193 merged the family-state/acceptance-matrix reconciliation; Foundation #1186/#1187 and Operations #951 were superseded/closed.
- Production release 36115559861 failed at Cloudflare API error 6111 (invalid Authorization header format during zone lookup). Current-head production is not certified.
- Nightly preflight 36115559932 failed with public Worker HTTP 000; nightly 36115573281 was cancelled by the exact production gate. No new provider-backed 24-program receipt exists.
- Live extractor benchmark 36115560009 passed: 40 receipts, provenance 1.0, route provenance 1.0, repeat reliability 1.0, 0 unstable groups, 4 ok / 32 empty / 4 blocked. Artifact 10855326519; digest sha256:1890da70d49377f2f89ee11daa644882a90972666916c07e7aa4edc8066c449e.
- Cloudflare: account role Super Administrator - All Privileges; heroic-ai.dev pending with activation failure reason unresolvable; custom domain enabled on foundation; deployed Foundation provenance github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c; deployed Operations provenance github:a3171f353539f1a31020c432f98cf0530cbf91ef; D1 research-intelligence ID 19f51638-47a5-4218-a9dc-73dbfd6156fe.
- Current Foundation main family-integrity workflow already uses actions/create-github-app-token and current main no longer contains the closed operations#352 target.
- ChatGPT/UI state is transport state only. Use this override as the cross-chat continuation point and refresh live refs before mutation.

---

# LIVE GITHUB + CLOUDFLARE SYNC AUDIT — 2026-09-25

This file is the durable cross-surface snapshot for the current audit.