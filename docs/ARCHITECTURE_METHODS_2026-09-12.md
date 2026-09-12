# Architecture Methods — 2026-09-12

Foundation is the public-safe place to define reusable semantics that should remain stable across the family.

## Public contract principles

1. Small immutable contracts beat duplicated ad-hoc dictionaries.
2. Evidence identity, provenance, freshness, and uncertainty are explicit fields.
3. Network failure, blocked access, empty data, invalid data, and successful absence are distinct states.
4. Hashes and schemas are validated at boundaries.
5. Public-safe contracts must not encode private provider policy or protected evaluation holdouts.

## Comparative findings applied to Foundation

Schema-first extraction systems favor an explicit output schema. High-performance LLM runtimes favor reusable context/cache identities. GitHub's current repository instruction model favors short repository-wide rules plus path-specific guidance. Cloudflare favors typed bindings and explicit lifecycle/rate-limit controls instead of scattering provider calls through business logic.

The family consequence is that Foundation should remain the smallest stable contract layer while Operations and Extractor-mapper supply private policy and execution behavior.

References:
- https://github.com/PaddlePaddle/PaddleNLP/blob/develop/slm/applications/information_extraction/taskflow_doc.md
- https://github.com/vllm-project/vllm/blob/main/docs/design/prefix_caching.md
- https://docs.github.com/en/copilot/reference/customization-cheat-sheet
- https://developers.cloudflare.com/workers/runtime-apis/bindings/
