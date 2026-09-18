# GitHub Family Architecture

The family has exactly two active repositories and one canonical owner per behavior. The normative ownership contract is `docs/FAMILY_CONTRACT.json`.

## Repository roles

| Repository | Canonical responsibility | Must not become |
| --- | --- | --- |
| Foundation | public-safe contracts, deterministic core, public evidence structures, public Worker/frontend, GitHub CI, canonical production deployment and backup | private policy, private runtime authority, protected provider/resource decisions |
| Operations | protected policy/governance, private acquisition/execution, provider/runtime, evaluation, promotion/recovery, chatbot orchestration | duplicate Foundation algorithms or a second family-wide authority |

The standalone extractor-mapper repository is historical. Active extractor/mapping responsibilities are under Operations.

## Canonical dependency

`Foundation public contract/core -> pinned Operations consumption -> private execution/policy -> verification/evaluation -> promotion/release`

Foundation never imports Operations internals. Operations materializes the pinned public Foundation core; generated public-core materialization is not a second authority.

## Internal placement

Foundation deterministic/public code belongs under public-safe packages. Operations owns private acquisition/extraction, protected policy, resources, chatbot orchestration, evaluation and promotion.

Repository location is itself an authority/security claim and changes deserve the same scrutiny as policy changes.

## Cross-repository policy

Shared changes must identify the owner, dependency direction, counterpart impact and evidence level. A consumer may fail closed, but must not become a competing policy engine.

If the counterpart repository cannot be inspected, record `UNKNOWN` rather than inventing a product defect.

## External architecture references

External architecture patterns may inform placement and reliability—separation of acquisition/mapping, durable state/checkpoints, explicit tool boundaries, provider routing, caching, idempotency and bounded workflows—but they are references, not copied business logic or authority.

## Validation and controls

Foundation owns public GitHub-hosted CI and canonical production deployment/backup workflows.

Operations intentionally has no GitHub-hosted private runtime workflow dependency.

Privileged Foundation workflows must run only from trusted `main` or approved manual dispatch, never pull-request code. Third-party actions are pinned. Credential-bearing deployment and backup purposes remain separate.

## Storage and cost

Backblaze B2 is the current artifact/backup store; D1 is compact operational metadata/index storage. R2 is historical and requires a new architecture/cost decision before reconsideration. Strict zero-cost remains a family invariant.
