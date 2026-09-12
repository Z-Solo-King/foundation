# Public Run-Record Boundary

Status: public contract guidance — 2026-09-12
Owner: Foundation

Foundation does not own private chatbot run history. It defines the public-safe observation/evidence fields that can participate in a durable run record.

## Public-safe fields

Foundation contracts may expose bounded values such as:

- schema version;
- research/run identifier when already public-safe;
- execution status;
- source identity;
- source lineage;
- observation identifiers;
- evidence references;
- temporal scope;
- content/document hashes;
- claim/evidence verification status;
- contract version;
- deterministic method identifier;
- bounded resource metrics when useful for public evaluation.

## Private fields that stay outside Foundation

Do not place these into public Foundation contracts:

- credentials or access tokens;
- private prompts or private user content;
- protected Operations policy snapshots;
- private provider billing/quota details;
- evaluation holdouts;
- private repository topology;
- private Cloudflare account identifiers/secrets;
- hidden model chain-of-thought;
- internal promotion or rollback decisions.

## Evidence rule

A run record is not evidence by itself. The canonical evidence graph remains the authority for claims. Run records point to evidence artifacts and verification state; they must not replace evidence provenance.

## Integration rule

Operations may wrap Foundation public observations in its private `ChatbotRunRecord`. Extractor-mapper may emit bounded execution observations. Foundation must not implement a second private run logger or make protected trust/promotion decisions.

## Versioning

When a public observation/evidence contract changes:

1. bump the relevant schema/version;
2. add boundary regression fixtures;
3. update the family contract/index;
4. preserve backward compatibility only through a compatibility boundary owned by the canonical contract layer;
5. let Operations and Extractor-mapper consume the new contract rather than copy it.
