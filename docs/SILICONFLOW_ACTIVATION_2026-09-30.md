# SiliconFlow Activation Boundary — 2026-09-30

Foundation activates SiliconFlow through the protected `production-secret-sync` environment only.

- Provider: `siliconflow`
- Model: `Qwen/Qwen3.5-4B`
- Runtime endpoint: owned by reviewed code, not a user-controlled secret
- Credential input: `SILICONFLOW_API_KEY`
- Cerebras is not activated by this change because no Cerebras credential is supplied.
- Mistral is not part of the provider fleet.
- Paid fallback, unknown pricing, auto-recharge and auto-upgrade remain disabled.

Runtime eligibility still requires fresh provider probe evidence; configuration alone does not establish availability.