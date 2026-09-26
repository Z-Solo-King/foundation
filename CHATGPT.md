# ChatGPT (chat-mode) project context

This is the thin adapter for plain **ChatGPT chat sessions** (Plus/Go, "Think"/Thinking mode — **not** Codex, no repo connector), matching the role `CLAUDE.md` and `GEMINI.md` play for their agents.

Unlike Claude Code / Gemini CLI / Codex, plain ChatGPT chat has **no automatic file-import mechanism**. It cannot `@import` this project's docs. Everything below exists because that gap has to be closed manually, once per session.

## Canonical sources
1. `docs/AI_AGENT_EXECUTION_POLICY.md` — governs work-cycle structure, parallel-lane strategy, session/context budget, checkpoint discipline, CI polling discipline, issue triage (R/C/E/H), evidence ladder. **Follow it exactly; do not re-derive it.**
2. `AGENTS.md` — cross-agent execution map.
3. `REPOSITORY_MAP.json` — repo/ownership map.
4. `docs/PROMPT_TO_CANONICAL_DOC_MAP.md` — before writing a long wishlist prompt, check this file first. Most recurring asks (repo structure, security, GitHub Actions boundary, chat continuity) already have a canonical answer here; it turns a paragraph into a one-line pointer.

If a GitHub connector is available in the session, read source #1 directly at session start. If not, the boot prompt below carries a compact summary that stands in for it.

## Session boot prompt
Paste this at the start of every ChatGPT session (or save as a Custom Instruction / saved prompt so it's not retyped):

> Load context from Z-Solo-King/operations and foundation. Read `docs/AI_AGENT_EXECUTION_POLICY.md` first — follow it exactly, don't re-derive it. Before I describe a task at length, check `docs/PROMPT_TO_CANONICAL_DOC_MAP.md` for whether it's already answered there. Use 4-6 parallel lanes per that doc's lane types (§3). Default to "keep going until completed, within the 20-minute session limit" unless told otherwise — never treat "don't stop until finished" or "100% coverage" as the instruction; use the bounded phrasing only. At session end, or if responses slow down or a step gets stuck, checkpoint per §4/§12/§13 of that policy and stop — don't keep polling or retry-looping. Classify any issue work as R/C/E/H (§9) before touching code. Don't paste large logs back — cite file ranges, run IDs, and hashes instead.

## Known ChatGPT-chat constraints this adapter exists to work around
- **No automatic context loading** — the model only knows what's pasted into the current session.
- **~20-minute practical Thinking-mode ceiling** for this project (policy §4), kept under the platform's own longer limit as a safety margin.
- **No persistent tool/session state between chats** — resume a fresh chat from the last recorded checkpoint (commits, run IDs, open-issue queue), not from conversation history.
- **Long/tool-heavy conversations degrade** — OpenAI's own troubleshooting guidance is to start a new chat rather than push a slow/stuck one further; this project's checkpoint discipline exists specifically so that's cheap to do.
- **A continuation instruction is genuinely required every session** — ChatGPT chat defaults to one bounded step per turn without one. The fix is using the *bounded* phrase above, not omitting the instruction and not making it unbounded ("don't stop until finished," "100% coverage," "don't ask me") — unbounded phrasing has no defined stopping condition and is a likely contributor to sessions going unresponsive.

## Non-goals
This file does not change production runtime authority, and it does not replace `docs/AI_AGENT_EXECUTION_POLICY.md` — it exists only to get that policy in front of a chat surface that can't load it on its own.
