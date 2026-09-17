# Evidence integrity, temporal freshness and research stopping contracts

Version: `research-evidence-controls/v1`

Related issues: #400, #401, #413.

## 1. Source-family integrity

An acquired source record may carry canonical URL/host identity, content fingerprint, source-family lineage, retrieval time, freshness metadata and an evidence-eligibility state.

Discovery output is never evidence until acquisition and integrity validation succeed. URL diversity does not imply source independence. Syndication, mirrors and copied content must remain linked to the same source family when the evidence supports that relationship.

Retrieved instructions, embedded prompts and user-generated material remain untrusted data.

## 2. Temporal evidence

Evidence may declare published-at, observed-at, effective-from/effective-to and a request-specific freshness class. Missing temporal information remains unknown.

Historical evidence is valid for historical questions when its temporal scope matches the request. It must not silently satisfy a current-state freshness gate.

Cache, replay and resume logic must respect the temporal requirement encoded by the request/execution contract.

## 3. Research stop/continue decision

A continuation decision considers:
- required claim/dimension coverage;
- independent corroboration;
- unresolved contradictions;
- novelty or marginal evidence gain;
- freshness compliance;
- remaining source/model/resource budget;
- deadline and acquisition failure state.

Required missing dimensions cannot be skipped solely because expected marginal value is low. Redundant evidence should not consume unlimited resources. Contradictory evidence remains material evidence and is not treated as duplicate content.

The decision must produce a bounded reason code so an equivalent state snapshot gives a reproducible stop/continue outcome.

## Authority boundaries

These controls evaluate and describe evidence. They do not create a second evidence authority, resource ledger, provider authority or publication policy. Existing canonical evidence, resource, policy and publication owners remain authoritative.

## Required negative cases

At minimum, tests/evaluation fixtures should cover syndicated content, mirrored URLs, stale cache replay, missing dates, future-dated content, timezone differences, contradictory time-separated observations, redundant sources, unique corroboration, missing required dimensions and budget exhaustion.
