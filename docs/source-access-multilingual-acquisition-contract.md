# Source access, multilingual evidence and bounded acquisition fallback

Version: `source-acquisition-controls/v1`

Related issues: #402, #406, #411.

## Source access, retention and disclosure

Source access is separate from evidence truth. A source policy may declare permitted acquisition methods, required authentication, access restrictions, retention class, raw-content versus metadata retention, public/private disclosure eligibility, revalidation requirements and deletion/expiry behavior.

A successful fetch does not by itself authorize unrestricted retention or publication. Unknown restricted-operation policy remains denied until the relevant authority is resolved.

## Acquisition fallback

Acquisition lanes may include deterministic/static fetch, structured data, search discovery and authorized browser execution. Each lane declares capability, authorization, resource cost, safety state and its permitted fallback relationship.

Escalation is bounded by the parent execution budget. Search output is discovery data, not evidence. Browser/XHR/embedded-state observations remain provenance-bearing source material.

Source safety, redirect validation and SSRF controls apply to every resolved destination regardless of acquisition lane.

## Multilingual evidence

Research records retain source language, original span identifiers and translation/normalization artifact identity where used. Translated/model-derived text remains derived evidence and cannot silently strengthen the underlying source.

Normalization must preserve dates, quantities, units, negation and important qualifiers. Mixed-language sources may retain per-span language where needed.

## Authority boundaries

These contracts do not create another source, evidence, resource or publication authority. Existing canonical policy/evidence/resource owners remain authoritative.

## Required negative cases

Include restricted retention, missing policy, public/private disclosure mismatch, browser escalation after deterministic failure, duplicate fallback attempts, multilingual negation, translated numbers/dates, mixed-language claims and translation/source contradictions.
