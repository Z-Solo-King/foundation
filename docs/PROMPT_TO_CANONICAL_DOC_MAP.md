# Prompt-to-canonical-doc map

Purpose: most recurring asks (repo structure, security, GitHub Actions boundary, chat continuity) already have a canonical answer somewhere in this repo family. Re-explaining the whole wishlist every session costs time, tokens, and is a large part of why long sessions stall. Use this file to turn a paragraph into a one-line pointer.

## How to use this

Instead of pasting the full ask, paste: *"Follow `<doc>` for `<topic>`."* The boot prompt in `CHATGPT.md` already does this for the execution policy; this file extends the same pattern to the other recurring topics.

## Map

| If you're about to ask for... | It's already answered in |
|---|---|
| No duplicate code, canonical placement, one owner per authority | `AGENTS.md` — "Canonical-owner rule" |
| Public repo not exposing secrets across full history, not just search-indexed spot-checks | #1265 (open), PR #1279 / PR #1280 (near-duplicate open PRs adding full-tree + git-history secret scan — check which is canonical before touching either) |
| GitHub Actions ownership / who's allowed to run workflows | `AGENTS.md` — "GitHub Actions ownership boundary" (Foundation is the sole Actions/CI/CD owner; Operations must never gain a workflow file) |
| Foundation ↔ Operations sync / pin drift | PR #1278 ("sync Foundation to current Operations main"), `docs/CURRENT_SOURCE_OF_TRUTH.md` |
| Google Merchant XML feed discovery/verification status per retailer | PR #1248, #1249 ("Custom/API Google Feed Recovery — chat handoff"), #1247 (WooCommerce, 9 unresolved retailers) |
| V18/V175 extractor-mapper port scope and exclusions (what's ported vs. deliberately left out) | PR #1275 (text/identifier normalization), PR #1276 (domain packs) — both explicitly exclude CAPTCHA/Cloudflare/anti-bot-evasion logic; see #348 for the tracked gap |
| Public-action boundary / private repo action execution | PR #1253 ("enforce public GitHub action boundary") |
| Long-term maintainability, AI+human-readable code, language migration policy | `AGENTS.md` — "Hybrid implementation policy" / "AI model portability", `docs/AI_PORTABLE_ENGINEERING_CONTRACT.md` |
| Chat-limit continuity / resuming a fresh chat without losing progress | `docs/CURRENT_SOURCE_OF_TRUTH.md`, `AGENTS.md` "ChatGPT continuity" sections, `CHATGPT.md` |
| Nightly research / 24-program acceptance run status | #157 (open, high-comment-volume tracker) |
| Exhaustive Research Intelligence Engine coverage | #58 (open, META tracker) |
| Cross-language benchmark/eval matrix for AI agents | #1157 |
| "Don't stop working" / sustained execution in one session | **Do not** ask for unbounded/100%/"don't stop until finished." Use `docs/AI_AGENT_EXECUTION_POLICY.md` §4's exact phrase: *"Keep going until completed, within the 20-minute session limit."* See note below. |

## Why the exact phrasing matters

ChatGPT (chat mode) defaults to one bounded step per turn unless told otherwise — an explicit continuation instruction is genuinely required every session, that part of the habit is correct. The failure mode isn't giving that instruction, it's giving an *unbounded* one:

- "Keep going until completed, within the 20-minute session limit" → bounded, checkpoint-aware, matches `docs/AI_AGENT_EXECUTION_POLICY.md` exactly, produces steady resumable progress.
- "Don't stop until finished / 100% coverage / don't ask me" → no ceiling, no checkpoint trigger, fights the project's own evidence-gate and session-budget rules, and is a likely contributor to sessions going unresponsive.

Same intent (don't stop after one step), opposite outcome, because only one of them has a defined stopping condition.

## Maintenance

Add a row here whenever a new recurring ask surfaces, instead of re-explaining it inline in a future session.
