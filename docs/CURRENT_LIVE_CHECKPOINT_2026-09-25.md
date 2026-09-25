# Current Live Checkpoint — 2026-09-25

## GitHub
- Foundation main: `52993de7651a9272802d6beff0932517fe3aff2a`
- Operations main: `45c715d52671793988d70e71ceacd0be9c629256`
- Open issues: 10 total — Foundation #1157/#58/#157; Operations #699/#603/#597/#385/#340/#197/#145.
- Open implementation PRs: 0.
- Remaining open PRs: Operations Dependabot #914/#915 only; no production/runtime work is attached to them.

## Agent tree and AI benchmark
- Foundation PR #1156 is merged.
- Operations PR #917 is merged.
- Foundation issue #1155 and Operations issue #916 are completed.
- Foundation issue #1157 remains open for the first real multi-model/agent baseline and retained per-run artifacts.
- Canonical benchmark lanes: A Planning & architecture; B Code & implementation; C Testing & verification; D Research & evidence; E Security/reliability/recovery; F Cross-language/tooling portability.
- Benchmark observations never override policy, security, provenance, resource, runtime, or deployment gates.

## Cloudflare
- Public Worker identity: `foundation`; current Cloudflare release annotation: `github:a1da7d115c69b9f9df21bd2c6d60dd2b717f232c`.
- Private Worker identity: `operations`; current Cloudflare release annotation: `github:a3171f353539f1a31020c432f98cf0530cbf91ef`.
- GitHub main is newer than these runtime references; this is expected while production promotion remains blocked/uncertified.
- Cloudflare `heroic-ai.dev` zone lookup returned HTTP 200 with no matching zone.
- Cloudflare Worker-domain lookup for `heroic-ai.dev` returned HTTP 200 with no matching attachment.
- Do not infer production certification from GitHub main or green repository checks.

## Runtime / research
- #197 remains open for the complete live Heroic-Ai.dev acceptance matrix.
- #157 remains open for a real 24-program provider-backed nightly execution with complete artifacts and exact provenance.
- Existing completed extractor benchmark evidence remains historical evidence; it does not certify the current public deployment.

## ChatGPT continuity
Treat the visible ChatGPT session as transport state, not as the engineering ledger. Before mutation, refresh live GitHub state and the current Cloudflare control-plane state when relevant. Preserve issue/PR, revision, evidence rung, artifact/provenance, blocker, and next action in GitHub.
