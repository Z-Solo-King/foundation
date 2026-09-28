# Heroic AI Overnight Research Run

The public Foundation repository owns the nightly research evidence workflow. Heroic AI is the product; this run is a maintenance and learning capability behind the assistant.

## Window

The scheduled kickoff is **01:00 IST** (**19:30 UTC** on the previous day). The workflow also starts from successful completion of the production-release workflow for the exact certified Foundation SHA, avoiding a long polling wait. Scheduled/manual invocations use only a short reconciliation window; a later successful production release causes a new `workflow_run` execution. The complete run remains bounded for the **09:00 IST** maintenance-window boundary.

## Coverage

There are 24 nightly programs: 8 programs in each of three logical lanes. They execute through one work-conserving **CrossFire** scheduler with a single global capacity of 20 active agents. This removes lane-local capacity fragmentation and lets newly free agent slots immediately serve another program, including while a prior program is synthesizing. After execution, the workflow materializes the same three lane artifacts and validates each exact eight-program set; the summary validates all 24.

No silent deterministic dry-run is permitted for the scheduled workflow; missing live executor configuration is a hard failure.

## Evidence

Each lane uploads and attests its JSONL result. The summary combines all three lane artifacts, produces the project-improvement report, compares it with the previous successful nightly baseline when available, and attests both summary and baseline.

Model findings remain candidate-only until they have the required acquisition/evidence receipt. A nightly result is not an authority for policy, security, billing, identity, resource limits, or publication correctness.

## CrossFire execution contract

The CrossFire name describes the scheduling pattern, not a new authority: independent programs share a bounded execution pool while existing provider, resource, policy, provenance and evidence authorities remain unchanged. The scheduler preserves deterministic result ordering after concurrent execution. Synthetic scheduling measurements may demonstrate throughput improvements, but they do not replace live provider-backed 24-program acceptance.