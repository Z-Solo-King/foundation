# Token-efficiency output floor

This document specifies the guard proposed by #373.

A token-efficiency gate must not reward a candidate merely because it produces fewer tokens. For the non-increasing-total-token path, the candidate must also preserve a minimum amount of substantive output relative to the baseline.

The floor is a backstop for efficiency comparison. It does not replace correctness, completeness, evidence coverage, or acceptance evaluation.

## Contract

For a candidate with `accepted=true` and non-increasing total token use:

`candidate.estimated_output_tokens >= max(absolute_floor, baseline.estimated_output_tokens * minimum_output_ratio)`

The concrete defaults must be chosen from benchmark evidence rather than arbitrary production assumptions.

## Required tests

- baseline and candidate with equal output pass when token use is non-increasing;
- candidate with materially truncated output fails despite lower token use;
- absolute floor handles tiny/zero-output baselines deterministically;
- ratio is validated as a bounded value;
- additional-token candidates continue through the existing evidence-retention path;
- the floor cannot be bypassed by manipulating `accepted` or cache-hit metrics.

## Authority boundary

The output floor is an efficiency safeguard only. It must not become a replacement for answer completeness or evidence verification. Existing quality/evidence authorities remain canonical.
