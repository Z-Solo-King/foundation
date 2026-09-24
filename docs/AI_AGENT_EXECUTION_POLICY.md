# AI Agent Execution & Context-Budget Policy

**Effective: 2026-09-24**

This policy keeps long engineering sessions bounded, resumable, and cheap to reason over. It applies to AI-assisted repository work and does not change production runtime authority.

## 1. Separate work surfaces
- GitHub lane: repository source, issues, pull requests, CI, tests, artifacts, and GitHub-side evidence.
- Cloudflare lane: Workers, D1, bindings, secrets/configuration, deployment state, runtime probes, and production receipts.
- Do not run both connector families in one work loop when the connector environment does not reliably support both.
- Shared state is carried by repository checkpoints/documents, not by re-reading an entire prior chat.

## 2. Bounded execution
A work cycle has four phases:
1. Non-mechanical diagnosis: understand the contract, inspect the smallest relevant evidence, and identify root causes.
2. Mechanical repair: make only fixes directly justified by those root causes.
3. Targeted verification: run only affected tests/workflows and inspect only relevant failures.
4. Checkpoint/reconciliation: record heads, run IDs, PRs, evidence level, and remaining blockers.

Default budget per cycle:
- up to 12 repository read/search operations;
- up to 6 file/log detail reads;
- up to 4 write operations grouped into at most 3 PRs;
- up to 4 verification/status polls per active workflow;
- no recursive expansion into a new repair cycle without a fresh checkpoint.

When a budget is reached, stop the cycle and checkpoint rather than continuing indefinitely.

## 3. Tool-output limits
- Prefer targeted search, exact file ranges, and failure-line extraction.
- Do not dump complete workflow logs or large source files when a focused slice is sufficient.
- Treat large artifacts as evidence sources; record artifact IDs and concise findings rather than repeatedly reloading the whole artifact.
- Reuse already verified SHAs/results until the relevant ref changes.

## 4. Polling and CI
- Never poll a running workflow in a tight loop.
- Record the run ID and check again only at meaningful phase boundaries.
- A queued/in-progress run is not itself a reason to keep the chat active.
- Do not start a replacement run merely because the current run is still running.
- Newer commits should supersede older analysis; stale runs become historical evidence.

## 5. Parallelism
Use parallelism only for genuinely independent reads or repairs. Keep fan-out bounded, normally 2-4 lanes. Each lane returns a compact result: root cause, files, proposed fix, verification target.
Do not create many parallel lanes that all require continuous polling.

## 6. Repair discipline
- One confirmed root cause -> one focused patch.
- Prefer one consolidated PR per closely related repair family.
- Do not modify canonical runtime authority to make a shadow/migration test pass.
- Do not close an issue when only L1/L2/L3 evidence exists for an L4 acceptance requirement.
- Never infer Cloudflare deployment state from GitHub source/CI alone.

## 7. Chat/session safety
OpenAI's current troubleshooting guidance recommends starting a new chat when a conversation is long or has many turns, and recommends checking service status when ChatGPT is slow, frozen, or stuck on Thinking/Generating. Keep engineering cycles short enough that a new chat can resume from the checkpoint without reconstructing the entire history.
Operational rule: do not continue a large repair loop just to satisfy a request to keep going until done. Complete the current bounded cycle, checkpoint it, and resume in a fresh chat when the cycle budget or context size becomes large.

## 8. Mandatory checkpoint contents
Every completed cycle records:
- current Foundation and Operations SHAs;
- open issue/PR counts;
- changed PRs and merge status;
- latest relevant workflow run IDs and conclusions;
- artifact IDs for benchmark/evidence outputs;
- L1/L2/L3/L4 evidence classification;
- unresolved external/runtime blockers;
- the next bounded action.

## 9. Recommended work order
Diagnosis first -> minimal repair batch -> targeted verification -> checkpoint -> next chat/cycle.
This order is intentionally preferred over repeated scan/fix/poll/re-scan loops.

## 10. Source
OpenAI Help Center, Troubleshooting ChatGPT Error Messages:
https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages