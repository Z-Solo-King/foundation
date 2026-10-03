# Nightly benchmark AI cross-fire — 2026-10-03

## Purpose

The canonical autonomous benchmark remains deterministic and authoritative. This workflow adds a separate six-lane AI cross-fire that observes the benchmark receipt and produces advisory diagnostics.

## Execution

The cross-fire runs nightly after the benchmark window and may also be started manually with a completed benchmark run ID. Six Workers AI models receive the same bounded evidence payload in parallel:

- `@cf/meta/llama-3.2-1b-instruct`
- `@cf/meta/llama-3.2-3b-instruct`
- `@cf/ibm-granite/granite-4.0-h-micro`
- `@cf/qwen/qwen2.5-coder-32b-instruct`
- `@cf/meta/llama-3.1-8b-instruct-fp8`
- `@cf/mistral/mistral-7b-instruct-v0.2-lora`

The lanes are independent and use a maximum parallelism of six. The aggregate is deterministic: it records transport success, schema compliance, latency, reported neurons, advisory assessment, flags, and agreement.

## Evidence boundary

Only the deterministic final benchmark receipt is sent to the AI lanes. The workflow does not execute downloaded artifacts, check out untrusted artifact code, dispatch another workflow, mutate GitHub, mutate Cloudflare, modify credentials or policy, or certify production/research completion.

Every receipt contains a SHA-256 digest of the bounded AI input and an explicit advisory-only authority marker.

AI output is invalid when it does not satisfy the required structured advisory schema. Generation success and schema compliance are recorded separately.

## Cost and runtime boundary

The live provider contract remains governed by the existing strict-zero-cost runtime policy. This workflow does not bypass provider selection or billing policy. A model/API failure becomes an unavailable advisory observation rather than a benchmark acceptance failure.

The benchmark itself remains responsible for its existing deterministic gates, including exact revision/provenance and truthful handling of missing or failed evidence.

## Live validation performed

A direct Cloudflare API cross-fire was executed independently before this workflow was proposed. The six selected models all returned successful API responses through the universal Workers AI endpoint. A separate logical evidence test confirmed that model responses can differ in formatting even when they receive identical facts; therefore the workflow measures strict schema compliance rather than treating any generated text as valid evidence.

The live test is supplemental runtime evidence. It does not close the 24-program nightly research acceptance issue.

## Relationship to the six-lane benchmark

The project-native benchmark already defines six analytical lanes and three repeats per task, with parallelism, adversarial testing, provenance, and hard-gate requirements. This cross-fire is an additional observation layer over those deterministic results; it does not replace the benchmark contract.
