# Documentation Hygiene

**Status:** normative; current.

## Canonical sources
- \`docs/CURRENT_SOURCE_OF_TRUTH.md\`
- \`docs/FAMILY_DOCUMENTATION_INDEX.md\`
- \`docs/KNOWLEDGE_LIFECYCLE_STANDARD.md\`
- \`docs/FAMILY_ARCHITECTURE.md\`
- \`REPOSITORY_MAP.json\`

## Documentation budget
Documentation volume is not itself a defect. Redundant context competing for the same fact is the defect.
Every active document must have a clear owner and purpose. Keep the AI normal read set small: index -> owner -> evidence. Do not require agents to load all of \`docs/\` for routine work.

## Naming and history
Active canonical docs use stable date-free names. Dated plans, audits, handoffs and receipts are historical unless explicitly current. When relocation helps, put them under \`docs/history/<topic>/\`. Do not create new session/handoff docs when an existing canonical owner can carry the state.

## Lifecycle
Preserve unique evidence/provenance. Remove pointer-only duplicates and repeated policy prose after dependency/reference checks. Prefer updating the canonical owner.

## Evidence language
Use states such as implemented, tested, merged, deployment-attempted, runtime-verified, blocked, deferred, superseded, obsolete, removed and historical. Never turn source/CI evidence into runtime/production claims.

## Privacy
Private credentials, protected runtime policy values, private source paths and sensitive control-plane details do not belong in public documentation.

## Maintenance
At milestones, deduplicate by semantic ownership rather than filename. Add a new document only when the knowledge has a distinct durable owner.

## Machine enforcement

The document lifecycle is now backed by a strict changed-file hygiene gate.

- `docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json` is the canonical formatting contract.
- `tools/repository_hygiene.py` enforces UTF-8, LF, final newline, trailing-whitespace, indentation, artifact and source-size hygiene.
- `tools/code_documentation_sync.py` enforces mapped code-to-document deltas.
- Full-repository debt is reported rather than mass-reformatted.
- The family coordinator checks Foundation/Operations contract parity without exposing private source contents.
