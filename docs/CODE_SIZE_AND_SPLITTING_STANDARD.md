# Code Size and Logic-Splitting Standard

## Why this exists

Large, hard-to-maintain files accumulate the same way documentation sprawl does:
one more responsibility gets added to an existing file because it's easier than
deciding where it actually belongs. No single addition looks unreasonable; the
accumulation is what becomes unmaintainable. This document sets concrete limits
and a concrete splitting procedure so the decision is made at write-time, not
during an emergency refactor later.

## Size limits (soft ceilings, not targets)

These are trip-wires that force a design decision, not laws to hit exactly:

- **Function/method: 40 lines.** Past this, a function is almost always doing
  more than one job. Extract the sub-steps into named functions even if each is
  only called once — the name documents intent that a comment would otherwise
  have to carry.
- **File/module: 400 lines.** Past this, check whether the file has one
  responsibility or several. A file can legitimately be long because it's one
  cohesive thing (a large state machine, a generated schema) — but that must be
  a stated reason, not a default assumption.
- **Class: 200 lines or 10 public methods.** Past this, look for a second
  responsibility hiding inside — usually a collaborator object trying to get
  out.
- **Function signature: 5 parameters.** Past this, group related parameters into
  a typed struct/dataclass/dict-with-schema instead of adding another positional
  argument.

A file or function over these limits is not automatically wrong. It requires a
one-line justification (in a comment or the PR description) for why it's one
cohesive unit rather than several. No justification means it's a split
candidate, not an exception.

## How to decide where to split (responsibility, not line count)

Splitting by responsibility, in order of preference:

1. **By what changes together.** If two blocks of logic are edited for
   different reasons on different timelines (e.g. one changes when a business
   rule changes, the other when a data format changes), they belong in
   different modules even if they currently look similar.
2. **By who calls it.** Code called only during setup/config belongs apart from
   code called on the hot path, even if both are short.
3. **By trust/authority boundary.** Code that enforces a public-safe contract
   (see this repo's `README.md` boundary description and `REPOSITORY_MAP.json`
   for where Foundation's authority ends and Operations' begins) must not live
   in the same module as code that merely consumes that contract. Mixing them
   is how a boundary gets silently crossed by a future edit.
4. **By I/O vs. logic.** Pure computation (given inputs, produce outputs, no
   side effects) should be separable from anything touching a network, database,
   filesystem, or clock. This is what makes the computation unit-testable
   without mocking half the world — directly relevant to `foundation_core`,
   which is meant to stay deterministic.

Splitting by line count alone (e.g. "cut this 800-line file into two 400-line
files at the midpoint") is not acceptable — it produces two files with no
coherent identity instead of one. Every extracted module must be describable in
one sentence that doesn't contain the word "and" describing two different
things.

## Procedure for splitting an existing large file

Do not split and rewrite at the same time — that makes it impossible to tell
whether a bug was introduced by the split or the rewrite.

1. **Characterize first.** If the file lacks tests covering its current
   behavior, add characterization tests before touching structure. The goal is
   to freeze current behavior as an oracle, not to judge whether that behavior
   is correct yet.
2. **Extract without changing behavior.** Move code into new files/functions
   with no logic changes — same conditionals, same edge cases, even ones that
   look like bugs. Note suspected bugs found during extraction as separate
   follow-up issues; do not fix them in the same change.
3. **Verify against the characterization tests.** The extraction is done when
   behavior is provably unchanged.
4. **Only then, in a separate change**, fix any bugs noted in step 2, now that
   they're isolated in a small, well-named unit instead of buried in the
   original file.

This mirrors the existing evidence-based standard in
`docs/ISSUE_EVIDENCE_STANDARD.md`: don't assert a split is safe without the
tests to prove it, the same way that document requires not asserting
duplication without reading the content.

## What this does not mean

- It does not mean splitting for its own sake. A short, cohesive file that
  clearly does one thing is correct at any line count under the ceiling, and
  artificially fragmenting it into more files does not improve maintainability
  — it just moves the same complexity into more places to navigate between.
- It does not mean every large file found during an audit gets a "split this up"
  issue filed reflexively. Per `docs/ISSUE_EVIDENCE_STANDARD.md`, a size ceiling
  being crossed is a lead to actually read the file and check for multiple
  responsibilities — not a conclusion to act on by line count alone.

## Practical checklist before adding to an existing large file

- [ ] Does this addition belong to the same responsibility as the rest of the
      file, per the "by what changes together" test above?
- [ ] If the file is already past a size ceiling, is there a stated reason it's
      one cohesive unit, or is this addition actually evidence it should split?
- [ ] If splitting: do characterization tests exist for the current behavior?
- [ ] If splitting: am I extracting only, with no behavior changes, in this
      change?
- [ ] If this refactor changes public boundaries, did I verify the affected
      import/ownership map before and after the extraction?
