# ChatGPT Session Observations

**Observed:** 2026-09-24

## Session execution observations

- Work was performed as a bounded engineering session rather than an unbounded scan/fix/poll loop.
- The conversation had accumulated stale checkpoints and large historical issue bodies; refreshing only the current head and current open-issue surface reduced noise.
- Parallel independent reads were materially more efficient than serially reopening every issue.
- A concrete repository defect was identified quickly from the current checkpoint: the chatbot smoke history reported `infrastructure_verify` versus `infrastructure_verify_public_test`. Current `main` already contains the corrected workflow contract, so no duplicate code fix was made.
- The nightly canary's failure-receipt path was found to lose structured evidence on pre-receipt failures. That was repaired so Worker HTTP status and bounded error fields are preserved.
- CI pile-up was identified as an execution-speed risk. Five expensive, supersedable Foundation workflows now cancel stale runs.
- GitHub and Cloudflare are permitted in one cycle by policy. In this session, the exposed tool registry did not provide an active Cloudflare action, so Cloudflare state was not claimed as freshly verified.
- Runtime/evidence gates were kept separate from repository defects; no issue was closed merely from deterministic CI evidence.

## Session safety rule

- **Project session cap: 20 minutes.**
- Sustained execution commands should include: **"Keep going until completed, within the 20-minute session limit."**
- Near the session boundary, stop launching new expensive scans, write a compact checkpoint, and resume from that checkpoint in a fresh chat/cycle.
- Observe session behavior after each cycle and update this document with concrete bottlenecks and improvements.

## Current optimization strategy

**Parallel diagnosis -> one consolidated repair batch -> targeted verification -> checkpoint.**

Target 4 lanes by default; expand to 6 only when lanes are genuinely independent. Avoid continuous polling and avoid feeding complete logs into the chat.
