# ChatGPT project adapter — current

Foundation and Operations share the Heroic AI project context. This file is a continuity aid, not a runtime authority.

## Canonical sources
1. `docs/AI_AGENT_EXECUTION_POLICY.md`
2. `AGENTS.md`
3. `REPOSITORY_MAP.json`
4. `docs/PROMPT_TO_CANONICAL_DOC_MAP.md`
5. `docs/CURRENT_SOURCE_OF_TRUTH.md`
6. `docs/FAMILY_SYNC_STATE.json`

## Session boot prompt
> Load context from Z-Solo-King/operations and foundation. Read `docs/AI_AGENT_EXECUTION_POLICY.md` first and follow it. Check `docs/PROMPT_TO_CANONICAL_DOC_MAP.md` before repeating a recurring task. Use 4-6 parallel lanes where applicable. Keep work within the project's bounded execution policy, checkpoint when the session budget is reached or a step stalls, and use live GitHub/Cloudflare evidence for current-state claims.

## Current ChatGPT platform facts
OpenAI currently documents that Projects keep related chats, files, and project instructions together and can reuse project context. Connected apps can be used in project chats when available and authorized. Project memory can reference project context depending on the selected memory mode. Starting a new chat is a supported troubleshooting step for long or unresponsive chats.

Official references:
- https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt
- https://help.openai.com/en/articles/8590148-memory-in-chatgpt
- https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages

Do not describe Projects as having no context. Do not assume arbitrary tool credentials or execution state persists across new chats.

## Connector evidence
On 2026-09-26 this project chat successfully used both Custom GitHub and Custom Cloudflare connectors in the same chat. This is empirical session evidence for this session.

## Continuity
Use `CURRENT_SOURCE_OF_TRUTH.md` and `FAMILY_SYNC_STATE.json` as the compact cross-chat checkpoint. Refresh live GitHub/Cloudflare before mutation. Update the canonical source-of-truth files when canonical behavior or production provenance changes.
