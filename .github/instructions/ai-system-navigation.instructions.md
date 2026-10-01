---
applyTo: "**"
---

# AI system navigation

Before broad retrieval, consult docs/AI_SYSTEM_DIRECTORY.md and docs/AI_SYSTEM_MAP.json.

Route work as:
intent -> category -> owner -> canonical path -> contract/policy -> tests -> workflow -> evidence -> runtime

Use the most-specific path. Search the other repository only when the directory says the responsibility crosses the Foundation/Operations boundary.

Keep category and authority separate. A category tells you where to look; it does not grant the component authority.

Do not treat telemetry-quality scores, AI model output, benchmarks, static scans, or CI as production authority unless the existing canonical promotion/evidence contract explicitly says so.

Unknown, unavailable, blocked, rejected, cancelled, timeout and error states must stay distinct.

For self-learning/self-evolution, produce only bounded candidate/evidence actions. Never mutate protected policy, credentials, resource limits, provider eligibility or production state from the navigation layer.
