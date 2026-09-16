# Evidence-Based Audit and Issue Standard

## Why this exists

A repository audit in this family previously filed and/or closed issues based on
filename pattern-matching and size/count heuristics instead of reading actual file
content. Three claims were made and had to be walked back in the same session:

1. A `backup/` directory was flagged as "dead weight duplicate content" — it
   contained only a `README.md` documenting a legitimate B2 backup workflow.
2. Two docs (`REPOSITORY_CONSOLIDATION_PLAN.md`, `REPOSITORY_DEDUP_AND_REVIEW.md`,
   in `operations`) were assumed to be overlapping "master plan" duplicates from
   their names — they serve different, non-overlapping purposes (one is a decision
   record of a completed migration, the other is an ongoing policy).
3. An open P1 issue (`foundation#154`) was flagged as contradicting stated
   architecture — the contradiction disappeared once the issue body and a
   cross-referenced doc were actually read; both described the same narrow,
   correctly-scoped problem.

The failure mode in all three: confident claims generated from names, counts, or
partial context, presented with the same certainty as claims backed by reading the
actual content. This document sets the rule so it stops happening, regardless of
whether the auditor is human or an AI assistant.

## Rules

1. **No duplication, dead-code, or "sprawl" claim without reading the content.**
   Matching filenames, matching prefixes, or a large file count in a directory is a
   *lead to investigate*, never a conclusion to report or act on.

2. **No issue is filed, closed, merged, or relabeled on the basis of a lead alone.**
   Before filing: read the file(s) in question. Before closing-as-duplicate: read
   both sides and confirm the overlap in content, not just in name.

3. **State what was actually checked.** An audit finding must say which files were
   opened and read, not just which files were listed. If only a directory listing
   was inspected, say so explicitly and label the finding as unverified — do not
   phrase it as a conclusion.

4. **Uncertainty is reported as uncertainty.** "This looks like it might be
   duplicated" is a valid, useful finding. "This is duplicated" when only the
   filename was checked is not — it's a false claim wearing the confidence of a
   verified one.

5. **Corrections are made on the record, not silently.** If a prior claim in an
   issue or PR turns out to be wrong after reading the actual content, the
   original issue/PR gets an explicit correction comment or is closed with the
   reason stated — it is not quietly dropped.

6. **This applies to code duplication too**, mirroring the methodology in
   `operations/docs/REPOSITORY_DEDUP_AND_REVIEW.md` (hash → AST → fingerprint →
   structural similarity, in that order of confidence) — the same discipline
   applies to docs, tests, and directories, which have no equivalent tooling yet
   and therefore rely entirely on the auditor actually reading them.

7. **Record repository revision when evidence can change.** Findings about current
   code, workflows, or issue state must include the inspected branch/commit when
   practical. A correct observation against an older revision is historical
   evidence, not proof of the present state.

## Practical checklist before filing a hygiene/cleanup issue

- [ ] I opened and read the actual file(s), not just their names/sizes.
- [ ] If claiming duplication, I compared the content directly (not just topic/title).
- [ ] If claiming something is dead/unused, I checked for references/imports, not
      just its location or a suggestive directory name.
- [ ] My issue states what evidence backs the claim, so a reviewer can verify it
      without redoing the whole audit.
- [ ] If I'm not fully sure, the issue title/body says so, rather than asserting.
- [ ] I recorded the relevant branch or commit when the finding is revision-sensitive.
