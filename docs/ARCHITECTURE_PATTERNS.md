# Architecture Patterns and Engineering Method

Foundation is the public contract and deterministic research layer. External systems are used as design references, not copied implementations.

## Patterns relevant to Foundation

### Contract-first research boundary
Keep typed requests, evidence certificates, deterministic planning, and the public API boundary independent from private policy and acquisition implementation. Private chatbot control belongs to Operations; network-heavy acquisition belongs to Extractor-mapper.

### Deterministic planning before inference
Normalize and validate requests, apply bounded resource rules, and select deterministic evidence/planning paths before invoking a model. Stable logic should not require an LLM.

### Evidence as a first-class object
Evidence must retain source role, provenance, confidence, and bounded identity. A model-generated statement is not equivalent to externally verified evidence.

### Replayable pure primitives
Prefer immutable contracts and small pure functions so research planning can be replayed and tested without network access. Side effects belong at the API or execution boundary.

### Small context envelopes
Keep public contracts compact. Large raw documents, credentials, private topology, and extractor implementation details do not belong in Foundation control envelopes.

## Method

Search the family for an existing authority, define the public contract, add deterministic validation, test failure semantics, then expose the smallest stable API surface. Do not move private provider, billing, promotion, or extraction policy into this repository.
