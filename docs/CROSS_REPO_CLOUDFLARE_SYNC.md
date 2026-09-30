# Cross-repo + Cloudflare synchronization record

Snapshot: 2026-09-30 (Asia/Kolkata)

## Authority model
- GitHub `main` trees are repository source truth.
- Cloudflare live API state is deployed-runtime truth.
- Fresh GitHub workflow evidence is the release certificate.
- Dated audits/handoffs are historical evidence.
- Production and research Operations pins are intentionally independent.

## Current repository state
- Foundation main: `97e16717e394316178b531a23fda69b2917b3a35`
- Operations main: `70daff88817d5ab62e7eab2d5dca45e32743f728`
- Production Operations pin: `ce4f9edbae3ddf1bf1c25a908d5bce014acc7676`
- Research Operations pin: `1a91efa53b9202f1624ddde892b0e86bd6b360f0`
- Operations contains no `.github/workflows`; Foundation owns automation.

## Current Cloudflare topology
- Pages project: `ai` -> `ai-cio.pages.dev`
- Public Worker: `heroic`, workers.dev disabled
- Private edge Worker: `operations-edge`
- Private core Worker: `operations`
- D1: `research-intelligence`
- Legacy `foundation` Worker: retired
- Retired Pages aliases: `heroic`, `heroic-ai`
- Dated probe Workers and their temporary Queue consumer: retired

## D1 verification — 2026-09-29
- `d1_migrations` exists and migrations 1–10 are applied.
- Direct `sqlite_master` inspection returned the operational tables and indexes.
- No DDL was changed by this audit.

## Security/runtime authority
- Production moderation policy is `block`.
- Strict zero-cost policy is enabled; paid/unknown-pricing fallback remains disabled.
- Production task-envelope verification uses a dedicated `TASK_SIGNING_ROOT`; its value is never stored in Git or documentation.
- Fresh production certification must verify the exact immutable Operations pin and post-deployment runtime behavior.

## Documentation hygiene
Do not copy secret values, Cloudflare account IDs, private Worker origins, mutable deployment IDs, or mutable issue counts into current public-state documents. Historical documents remain useful only as provenance.

## 2026-09-30 AI provider synchronization
Foundation currently activates seven external AI lanes: OpenRouter, Groq, Gemini, NVIDIA NIM, Cohere, Hugging Face, and SiliconFlow. Operations supports an eight-family private catalog, with Cerebras remaining unconfigured on Foundation because no credential is supplied. Cloudflare Workers AI remains the native in-Worker provider. Mistral is excluded from the production fleet. Provider credentials are not documented here. Current public contract: `docs/AI_PROVIDER_FLEET_2026-09-30.md`; private runtime contract: Operations `docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.md`.

## 2026-09-30 multi-lens / extractor-mapper synchronization
- Foundation main now contains the active multi-lens execution engine and planner contract.
- The planner is scheduling-only; acceptance and protected authority remain with existing owning contracts.
- Active extractor/mapper runtime remains under Operations `extractor_mapper/`; Foundation retains the public deterministic mapper core.
- The former standalone extractor-mapper repository is retired/deleted and must not be referenced as an active repository.
- Cloudflare deployment/runtime state is not inferred from these GitHub changes; it requires its own live runtime receipt.
