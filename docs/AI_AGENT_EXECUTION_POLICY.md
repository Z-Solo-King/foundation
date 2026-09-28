## 9. Acquisition source selection
Acquisition is capability-driven, not tied to one transport. Browser retrieval, direct HTTP/HTML, public APIs, feeds, structured page data and search discovery may all be used when available and appropriate to the requested data. A transport failure is a signal to select another available acquisition mode or record \`unresolved_transport\`; it is not by itself a data-negative result. Preserve source provenance and acquisition mode in evidence.

**Policy lock:** never add a project-wide rule that disables browser/API/feed/HTTP acquisition as a class. Route by requested data, source capability, runtime state, cost/resource budget, and evidence requirements.

## 10. Audit routing
\`docs/AI_AUDIT_SYSTEM.md\` is the routing guide; \`docs/AI_PROJECT_MAP.json\` is navigation metadata. Contracts, owner registries, source, tests and runtime receipts remain authoritative.
Large audits begin issue/context-first and use map-first retrieval, adaptive lanes, root-cause clustering and second-lens validation. Compute-inspired patterns are optional engineering analogies.

## 11. Migration / polyglot
Language changes are evidence-driven. Python remains protected semantic/policy/provenance/replay/resource authority until formal promotion. Candidates need contract, differential, adversarial, performance/resource, shadow, canary and rollback evidence.

## 12. Completion
Remaining work must be explicit \`RUNTIME\`, \`EXTERNAL/ADMIN\`, \`DUPLICATE/SUPERSEDED\` or \`ROADMAP\`, with canonical owner and missing evidence recorded.
