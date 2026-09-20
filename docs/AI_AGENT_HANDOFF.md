# AI Agent Handoff — Research Intelligence Engine

## 2026-09-19 CURRENT HANDOFF — AUTHORITATIVE

This section is the continuity anchor for the next maintenance chat. Current GitHub state and fresh production evidence override all older sections in this file.

### Exact repository state

- Foundation `main`: `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`
- Operations `main`: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation production Operations pin target: `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`
- Foundation nightly research pin remains: `9572b3b2d2c52120833a590b4612daacc2a493c2`
- Foundation PRs #739, #740, #741 and #742 are merged.
- Operations PRs #535, #536 and #537 are merged.
- Foundation #27 is closed.
- Operations contains no GitHub Actions workflow authority.

### Latest canonical production proof

Run `35456292033` (#232), Foundation `6a91fbd17143083882e9ac7ebfa52f0b06a344b2`, last verified against Operations `9572b3b2d2c52120833a590b4612daacc2a493c2`. The next production certification target is Operations `c6f7ebaec4ebdf21cd1d036df073b90de5bc7129`.

The release verified:

- public Worker deployment/readiness;
- private Operations Worker deployment and Cloudflare provenance `github:9572b3b2d2c52120833a590b4612daacc2a493c2`;
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
- #263 — one supported workflow-dispatch bridge receipt with exact target SHA and actual job creation remains missing.
- #452 — repository SSE lifecycle is green; remaining proof is real client cancellation/disconnect propagation and provider-error-after-partial-output terminalization.
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
- #385 — broader concurrent completion/failure/cancellation, crash-after-side-effect, late-output, and restart/recovery acceptance. The concrete stale-attempt defect is fixed and covered by the latest production CAS check.

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

When a queue item is RUNTIME_GATE or EXTERNAL_BLOCKED, record the exact missing evidence on the issue and move to the next independent lane.
