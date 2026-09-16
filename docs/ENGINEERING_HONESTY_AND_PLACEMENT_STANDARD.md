# Engineering Honesty, Placement, and Plain-Language Standard

## Why this exists

This covers three related failure modes not addressed by the existing size,
splitting, or evidence standards: code that performs configurability or
completeness it doesn't have ("vibe coding"), code placed by convenience rather
than responsibility, and documentation/comments written to sound impressive
rather than to state a checkable fact.

## 1. No pseudo-configuration ("vibe coding")

A concrete example was found in `operations/private/runtime_policy.py`:
`RuntimePolicy.strict_zero_cost_only: bool = True` is defined as a field — but
the validator that reads it immediately raises if it's ever `False`:

```python
if not policy.strict_zero_cost_only:
    raise PermissionError("strict zero-cost policy cannot be disabled")
```

The field looks configurable — it's a bool with a default, sitting in a
dataclass meant to be constructed with different values. It isn't; the only
legal value is `True`, permanently. This is not necessarily a bug (a hard,
non-negotiable cost policy can be the right call) — it's a *representation*
problem: the code claims a shape (configuration) that its actual behavior (a
constant) contradicts. A future maintainer has to trace the validator to
discover the field is fake, in either repository.

**Rule:** if a value can only ever be one thing, it is not a field on a config
object — it's a module-level constant, or an assertion with a comment
explaining why it's fixed. If it truly needs to look like a toggle for
call-site clarity, the code enforcing it must say so at the point of
definition, not several lines away in a validator the reader may not reach.

This generalizes: any parameter, flag, or config field whose only observed or
enforced value is a single constant is either dead flexibility (remove it) or
an undocumented invariant (document it where the false impression is created).

Other instances of the same family, to check for during review:

- A function parameter with a default that is never overridden anywhere in the
  codebase — dead flexibility, same as above.
- An `if/else` branch where one branch is unreachable given the actual caller
  set — either delete it or document why it's kept (e.g. future caller,
  external API contract).
- A try/except that silently swallows an exception "for now" — either handle
  it meaningfully or let it propagate; a bare except hiding a real failure is
  a false claim of success, the same failure family as a fake config field.
  For `foundation_core`, this matters especially: silently-swallowed
  exceptions in deterministic code break the determinism guarantee itself.

## 2. Logical code placement

The existing boundary description (this repo's `README.md`, `REPOSITORY_MAP.json`)
already states what Foundation is responsible for versus Operations. This
section applies the same idea one level down, to where code lives *within* a
repository:

- **One module, one authority.** A new deterministic-core concern gets its own
  named module under `foundation_core/`, not folded into an existing one
  because it happens to touch similar data.
- **Naming should tell you the authority, not just the topic.** Prefer a name
  that states what makes a module different (e.g. its specific normalization
  responsibility) over a generic name or a version-number suffix.
- **A file's location is a claim.** Placing code in `foundation_core/` is an
  assertion that it's public-safe, deterministic, and credential-free. Moving
  code into or out of that boundary should get the same scrutiny as changing
  an access-control rule, because it functionally is one.
- **Don't co-locate by coincidence of timing.** Two features built in the same
  session aren't automatically related; place each by the "what changes
  together" test in `docs/CODE_SIZE_AND_SPLITTING_STANDARD.md`.

## 3. Plain-language documentation ("humanizer")

Documentation in this family sometimes uses strong, absolute language —
"canonical," "authoritative," "deterministic," "the single source of truth" —
which is appropriate *when it's actually verified*, and misleading when it's
aspirational. The words aren't the problem; using them as a substitute for
evidence is.

**Rule:** a document may assert something is canonical/authoritative/complete
only if that claim is checkable against current repository state (a file
path, a test, a passing CI run). If the claim is a goal rather than a verified
fact, say so directly: "intended to be the canonical X" or "not yet verified
against Y," rather than stating it as settled.

This is the same discipline as `docs/ISSUE_EVIDENCE_STANDARD.md` applied to
prose instead of issue-filing. A reader — human or automated — should be able
to tell from the wording alone which claims in a doc are verified and which
are intended/aspirational.

**Practical tell:** if a sentence would need to change after actually running
the code, it's a factual claim and must be checkable. If it would still be true
regardless of what the code does today, it's a design intent and should be
worded as one.

**Revision scope:** when a statement depends on code, workflow, issue, or
runtime state, identify the repository revision or execution date that supports
it. This prevents a once-correct statement from becoming misleading after the
implementation changes.

## Practical checklist

- [ ] Does every config/flag field have at least one call site that sets it to
      something other than its default? If not, is that intentional and
      documented at the definition, not just enforced elsewhere?
- [ ] Does this file's location match what it actually does, not just what was
      convenient when it was written?
- [ ] Does this doc/comment state anything as settled fact that hasn't
      actually been verified against current repository state?
- [ ] For revision-sensitive claims, is the supporting revision or date clear?
