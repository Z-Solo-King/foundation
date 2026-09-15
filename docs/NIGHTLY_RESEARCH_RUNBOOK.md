# Heroic AI Overnight Research Run

The public Foundation repository owns the nightly research evidence workflow. Heroic AI is the product; this run is a maintenance and learning capability behind the assistant.

## Window

The scheduled kickoff is **01:00 IST** (`19:30 UTC` on the previous day). Three research lanes start in parallel. Their maximum execution time is bounded so the complete run is intended to finish before the **09:00 IST** maintenance-window boundary.

## Coverage

There are 24 nightly programs: 8 programs in each of three lanes. Each lane validates its own exact eight program IDs; the summary validates all 24.

Aggregate research capacity is 20 active agents per nightly run (`6 + 6 + 8`). No silent deterministic dry-run is permitted for the scheduled workflow; missing live executor configuration is a hard failure.

## Evidence

Each lane uploads and attests its JSONL result. The summary combines all three lane artifacts, produces the project-improvement report, compares it with the previous successful nightly baseline when available, and attests both summary and baseline.

Model findings remain candidate-only until they have the required acquisition/evidence receipt. A nightly result is not an authority for policy, security, billing, identity, resource limits, or publication correctness.
