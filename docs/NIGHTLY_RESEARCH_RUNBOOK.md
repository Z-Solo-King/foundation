# Heroic AI Overnight Research Run

The public Foundation repository owns the nightly research evidence workflow. Heroic AI is the product; this run is a maintenance and learning capability behind the assistant.

## Window

The 24-program research workflow is **not time-scheduled**. It accepts `workflow_dispatch` only. The canonical production-release workflow explicitly dispatches it after a successful release and preflight, passing the exact Foundation SHA, production release run ID, and deployed Operations revision. Manual dispatch remains available for controlled testing and explicit live runs.

A research workflow run therefore has two intentional launch paths: an explicit manual/API dispatch, or the post-release dispatch performed by the canonical production-release workflow. There is no 01:00 IST cron on the research workflow. GitHub's `schedule` event is intentionally absent so the research engine cannot wake up once per day merely because the clock reached the overnight window.

The complete run remains bounded by its workflow timeout and the existing executor/resource controls.

## Coverage

There are 24 nightly programs: 8 programs in each of three logical lanes. They execute through one work-conserving **CrossFire** scheduler with a single global capacity of 20 active agents. This removes lane-local capacity fragmentation and lets newly free agent slots immediately serve another program, including while a prior program is synthesizing. After execution, the workflow materializes the same three lane artifacts and validates each exact eight-program set; the summary validates all 24.

No silent deterministic dry-run is permitted for a live dispatch; missing live executor configuration is a hard failure.

## Evidence

Each lane uploads and attests its JSONL result. The summary combines all three lane artifacts, produces the project-improvement report, compares it with the previous successful nightly baseline when available, and attests both summary and baseline.

Model findings remain candidate-only until they have the required acquisition/evidence receipt. A nightly result is not an authority for policy, security, billing, identity, resource limits, or publication correctness.

## CrossFire execution contract

The CrossFire name describes the scheduling pattern, not a new authority: independent programs share a bounded execution pool while existing provider, resource, policy, provenance and evidence authorities remain unchanged. The scheduler preserves deterministic result ordering after concurrent execution. Synthetic scheduling measurements may demonstrate throughput improvements, but they do not replace live provider-backed 24-program acceptance.

## Evidence-hardening contract

The nightly pipeline follows the staged recovery pattern used by the feed-recovery work:

1. Capability preflight validates the actual research-agent response contract, not merely that an HTTP response contains text.
2. Coverage accounting records the exact 24 expected program IDs and separately records missing, unexpected, and duplicate results. A transport rejection, challenge, quota rejection, or provider failure is an execution state, not evidence that the research subject has no answer.
3. The CI proxy uses bounded transport recovery for transient failures while preserving the same idempotency key and keeping credentials and model responses out of logs.
4. The nightly acceptance manifest maps output to #58/#157 and explicitly keeps #597/#603 pending until their required private/local runtime receipts exist.
5. Migration evidence remains tiered: deterministic repository review is supporting evidence; #597/#603 require candidate-specific 32-case/3-repeat parity, security/policy/provenance/cancellation/timeout coverage as applicable, measured performance/conversion cost, shadow, canary, and rollback evidence.

Cloudflare Workers AI documents JSON Schema response formats and also notes that schema compliance is not guaranteed, so the caller must validate the returned structure before treating a generation as contract-compliant. The nightly preflight therefore tests the same structured research path used by the 24-program executor.

The production research path remains a loopback CI proxy to the authenticated Foundation Worker, which reaches private Operations through the service boundary and native Workers AI binding.

The workflow is dispatch-only. The successful production-release workflow is the controlled automatic launcher for a released SHA; the research workflow itself has no recurring cron trigger.


## Public/private research contract boundary

The public Foundation `ChatRequest` schema remains intentionally closed. `research_agent` is a private Operations execution capability and must not be placed in the public `/api/v1/chat` JSON payload.

The approved path is:

`authenticated client -> public ChatRequest validation -> X-Heroic-Research-Proof header -> Foundation boundary translation -> private Operations research_agent=true`

This preserves a strict public API while allowing the private research executor to receive its capability flag only after Foundation authentication and boundary validation.
