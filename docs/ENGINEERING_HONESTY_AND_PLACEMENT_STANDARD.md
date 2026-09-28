# Engineering Honesty, Placement, and Plain-Language Standard

## Purpose
Prevent fake configurability, code placed outside its real authority boundary, and documentation that presents an unchecked claim as verified fact.

## 1. No pseudo-configuration
A configuration field or branch must either have a real supported alternative path or be an explicit invariant at its definition. Apply the same test to unused parameters, unreachable branches and silently swallowed exceptions.

## 2. Logical placement
One module, one authority. File location is an architectural claim about safety and responsibility. Place code by the boundary it owns and by what must change together. Public-safe code must not depend on protected runtime authority.

## 3. Plain-language documentation
Use "canonical", "authoritative" and "complete" only when the claim is checkable against current source, tests, workflow evidence or a runtime receipt. Label design intentions as intentions and dated observations with date/revision.

## 4. Public/private documentation
Public documents may describe protected boundaries generically. Do not expose private source paths, secret names/values, control-plane details or protected implementation snippets.

## 5. Review
Check config alternatives/invariants, placement, revision traceability and public/private exposure.
