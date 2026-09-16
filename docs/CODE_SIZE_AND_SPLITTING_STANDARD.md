# Code Size and Logic-Splitting Standard

## Purpose

Large files accumulate responsibilities gradually. Size limits are design trip-wires, not targets.

## Soft ceilings

- Function/method: 40 lines.
- Module: 400 lines.
- Class: 200 lines or 10 public methods.
- Function signature: 5 parameters.

Crossing a limit requires a stated reason for remaining cohesive. It is not by itself proof of a defect.

## Split by responsibility

Prefer, in order:

1. what changes together;
2. who calls it and whether it is hot-path/setup code;
3. trust/authority boundary;
4. I/O versus pure computation.

Never split by arbitrary midpoint. Every extracted module must have one coherent responsibility.

## Safe procedure

1. Add characterization tests if current behavior is insufficiently covered.
2. Extract without behavior changes.
3. Run characterization tests and repository checks.
4. Fix discovered behavioral bugs in a separate change.
5. Recheck imports, public boundaries, and ownership.

Do not combine structural extraction with an unrelated bug fix.

## Checklist

- [ ] Same responsibility as existing code?
- [ ] Size ceiling crossed with a documented cohesion reason?
- [ ] Characterization coverage exists before structural refactor?
- [ ] Extraction-only change if refactoring?
- [ ] Public/authority boundaries verified before and after?
