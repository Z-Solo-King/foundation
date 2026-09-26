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
> Load context from Z-Solo-King/operations and foundation. Read `docs/AI_AGENT_EXECUTION_POLICY.md` first and follow it. Check `docs/PROMPT_TO_CANONICAL_DOC_MAP.md` before repeating a recurring task. Use live GitHub/Cloudflare evidence for current-state claims, keep sustained work within the project's bounded execution policy, checkpoint when the session budget is reached or a step stalls, and never treat an unbounded instruction such as “don't stop until finished” as a stopping condition.

## Current ChatGPT facts
OpenAI documents that Projects keep related chats, files, and instructions together; connected apps can be used in project chats when available; and project memory can use same-project context depending on memory mode. OpenAI also recommends starting a new chat when a conversation is long or unresponsive.

References:
- https://help.openai.com/en/articles/10169521-projects-in-chatgpt
- https://help.openai.com/en/articles/11487775-connected-apps-in-chatgpt
- https://help.openai.com/en/articles/8590148-memory-in-chatgpt
- https://help.openai.com/en/articles/7996703-troubleshooting-chatgpt-error-messages

Do not claim that ChatGPT Projects lack project context. Do not assume tool credentials or runtime state persist across arbitrary new chats.

## Connector evidence
On 2026-09-26 this project chat successfully used both Custom GitHub and Custom Cloudflare connectors in the same chat. Keep this as empirical session evidence.

## Continuity
Use `CURRENT_SOURCE_OF_TRUTH.md` and `FAMILY_SYNC_STATE.json` as the compact cross-chat checkpoint, and refresh GitHub/Cloudflare before mutation.
