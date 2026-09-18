# Family Maintenance Contract

**Status:** canonical public-safe structural maintenance policy  
**Scope:** Foundation + Operations repository structure and maintenance  
**Authority:** this contract governs structural hygiene; private runtime semantics remain in Operations' canonical private standards.

## Invariants

1. **One canonical owner.** A behavior, policy, schema, registry, route, resource authority or deployment boundary has one owner. Compatibility facades may translate interfaces but cannot reimplement authority.
2. **Public/private separation.** Foundation contains only public-safe contracts/core/UI/API/deployment/backup material. Private policy, credentials, holdouts, internal research/benchmarks, runtime internals and sensitive operational methodology remain in Operations.
3. **Operations has no GitHub Actions authority.** Operations must contain no active `.github/workflows/` directory. Foundation owns family GitHub Actions and canonical production deployment.
4. **No competing deployment authority.** Cloudflare Workers Builds/Deploy Hooks and secondary deployment scripts must not become another production owner.
5. **No active benchmark/research sprawl in Foundation.** Internal benchmarks, nightly research, autonomous scorecards and private performance/test assets belong in Operations. Foundation may retain only public-facing contracts or tests required to enforce the public boundary.
6. **One living document per responsibility.** Do not create parallel current-state, handoff, analysis-map, architecture, governance, limitation, or model-specific guidance files. Extend the canonical document and delete absorbed copies.
7. **Schemas/state are separate from prose.** Keep machine-readable contracts/state in JSON/schema files; do not duplicate the same authority in prose copies.
8. **Historical material is provenance, not authority.** Dated decision records, benchmarks, testing ledgers and archived code remain only when they preserve unique evidence or reproducibility. They must not be referenced as current authority.
9. **Archives are inert.** Retired code/workflows/tests may be preserved under Operations `private/archives/`; archived material is not a runtime owner and must not be imported as active implementation.
10. **Evidence tiers remain distinct.** Source/repository/CI/control-plane/runtime/production evidence must never be upgraded by wording.
11. **Minimal change discipline.** Search both repositories, identify the owner, inspect callers/side effects, make the smallest coherent change, add focused regression, then remove obsolete duplicates.
12. **Dynamic state is not documentation authority.** Do not maintain copied open-issue counts, branch tips, PR queues, deployment status or mutable runtime configuration as if they were current truth. Record observations with timestamps/revisions and always re-check live state before acting.
13. **No chat-driven proliferation.** A conversation limit, model change, or new agent does not justify another handoff/status/guidance document. Consolidate durable knowledge into the existing owner.

## Canonical living private-document roles

Operations maintains one canonical document for each of these roles:

- current state → `docs/CURRENT_SOURCE_OF_TRUTH.md`
- agent maintenance → `docs/AGENT_MAINTENANCE_GUIDE.md`
- family operating model → `docs/FAMILY_OPERATING_MODEL.md`
- governance/evidence → `docs/GOVERNANCE_AND_EVIDENCE_STANDARD.md`
- knowledge lifecycle/limitations → `docs/KNOWLEDGE_LIFECYCLE_STANDARD.md`
- future candidates → `docs/FUTURE_KNOWLEDGE_CATALOG.md`
- chatbot contract → `docs/CHATBOT_BOUNDARY.md`

Model/vendor-specific guidance is not a canonical role.

Current-state documents must identify their observation time and explicitly defer mutable facts to live repository/runtime state.

## Disallowed recurrence patterns

The following filenames are retired in the current family structure and must not be recreated as new canonical documents:

`AI_AGENT_HANDOFF.md`, `AI_ANALYSIS_MAP.md`, `CLAUDE_GUIDANCE.md`, `CODE_OWNERSHIP_AND_PLACEMENT.md`, `AI_AUDIT_AND_VERIFICATION_STANDARD.md`, `AI_GOVERNANCE_STANDARD.md`, `FAMILY_ARCHITECTURE.md`, `FAMILY_DOCUMENTATION_INDEX.md`, `GOVERNANCE_KNOWLEDGE_TAXONOMY.md`, `LIMITATION_KNOWLEDGE_STANDARD.md`.

Do not create equivalent copies under a different filename merely to bypass this list.

## Enforcement model

- Foundation PR checks run the local governance linter.
- Foundation's cross-repository drift workflow checks the private Operations tree for the same structural invariants.
- Tests and workflows enforce the deployment/Actions boundary.
- Human review resolves semantic duplication that static checks cannot prove.

A green structural check does not certify private runtime behavior.
