# Repository Control Patterns

Foundation follows repository-level controls that keep public contracts stable and inexpensive to consume. New controls should prefer contract validation, deterministic behavior, explicit compatibility, and immutable evidence over hidden side effects.

Key rules: version cross-repository contracts; validate before execution; keep serialization at boundaries; make compatibility additive where possible; keep public workflows least-privilege; pin workflow actions; and treat generated artifacts as outputs rather than sources of truth.

Feature proposals should be evaluated as capability candidates first. A candidate may be tested and benchmarked without becoming an operational dependency. Breaking changes require an explicit transition plan and regression coverage.

These rules complement the family ownership map rather than duplicating private Operations policy.
