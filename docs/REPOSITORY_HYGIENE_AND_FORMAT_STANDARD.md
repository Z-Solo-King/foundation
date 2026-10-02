# Repository Hygiene, Uniform Format, and Code–Documentation Synchronization Standard

**Status:** normative; current  
**Effective date:** 2026-10-02  
**Scope:** Foundation + Operations

## Purpose

This standard adds the missing machine-enforcement layer to the existing documentation and family-synchronization policies.

The objective is not to reformat the repositories indiscriminately. The objective is to make every new or modified change deterministic, readable, reviewable, and synchronized with the documentation that owns its meaning.

The governing rule is:

**one canonical contract, one formatter policy, one synchronization map, one evidence level, and one change gate.**

## 1. Canonical format contract

The machine-readable authority is:

- `docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json`

Foundation and Operations must carry the same contract version and the same contract bytes. The Foundation family coordinator checks this parity.

The project uses:

- **EditorConfig** for editor-neutral file basics such as UTF-8, LF endings, spaces for indentation, and final newlines.
- **Ruff** for Python linting and formatting.
- **Prettier** for JavaScript, TypeScript, JSON, YAML and Markdown formatting.
- **markdownlint-cli2** for Markdown structural/style linting.

Prettier intentionally uses a repository-local configuration rather than a global configuration so formatter behavior follows the repository with the code. Ruff provides a fast Python formatter/linter and supports `--check` for non-mutating CI validation. citeturn133518search0turn133518search1turn622704search0turn622704search3

## 2. Universal hygiene

All tracked text files must:

- be UTF-8;
- use LF line endings;
- end with exactly one final newline;
- contain no trailing whitespace;
- avoid tab indentation;
- not contain generated/cache artifacts that are forbidden by the contract.

The hygiene checker works on tracked Git files so ignored local artifacts do not become accidental repository policy.

## 3. Ratchet instead of mass-reformatting

Existing documentation and source debt is not silently rewritten just to make one governance PR large.

The strict PR gate applies to changed files. The full-repository audit is used for reporting and cleanup planning.

This prevents a formatter rollout from producing an enormous unrelated diff while still preventing new debt.

## 4. Code-size hygiene

Source-size thresholds remain responsibility-based rather than arbitrary:

- **attention:** more than 500 lines;
- **critical:** more than 1,000 lines or more than 50,000 bytes.

A critical threshold is a decomposition trigger. It is not permission to split code mechanically by line count. Modules should be separated by responsibility, authority, lifecycle or interface.

## 5. Documentation hygiene

Canonical current documents use stable names. Dated records are appropriate for historical audits, handoffs, receipts and snapshots and belong in their designated historical/runtime areas.

A new canonical document should not duplicate an existing owner merely because a new task or chat exists.

Every canonical document should have:

1. status;
2. owner/authority;
3. purpose and scope;
4. canonical implementation or contract paths;
5. evidence boundary;
6. synchronization expectations.

## 6. Code–documentation synchronization

The machine-readable map is:

- `docs/CODE_DOCUMENTATION_SYNC_MAP.json`

A sync group maps high-coupling code/configuration paths to their canonical documents.

When a mapped code path changes, at least one mapped canonical document must change in the same change set unless a declared exemption is explicitly recorded.

Documentation-only changes do not automatically require code changes. Documentation can clarify current state, evidence, architecture or procedure without modifying implementation.

The coordinator validates:

- every mapped document exists;
- every important code pattern resolves to at least one tracked path;
- no sync group is structurally stale;
- changed code paths have the required documentation delta;
- the current repository status is expressed using the uniform status/evidence vocabulary.

## 7. Cross-repository synchronization

Foundation is the family coordination point because it already owns public CI and the repository bridge.

The family coordinator performs read-only checks against Operations:

- formatter/config contract parity;
- synchronization-map schema validity;
- repository hygiene;
- code-documentation map validity;
- SHA and ownership metadata consistency.

The coordinator must not publish private source contents, credentials, private runtime identifiers or private document bodies. It reports counts and rule identifiers rather than sensitive file contents.

Operations remains the private runtime authority. Foundation remains the public CI/deployment authority.

## 8. Change workflow

For every material change:

1. identify the canonical code owner;
2. identify the canonical document owner;
3. make the code/configuration change;
4. update the owning documentation when the mapped contract changes;
5. update focused tests;
6. run the changed-file hygiene/format gate;
7. record the actual evidence class in the PR;
8. let the family coordinator detect cross-repository drift.

## 9. PR and issue coordination

Material PRs continue to use the Family Synchronization Standard fields:

- scope;
- canonical owner;
- non-goals;
- safety;
- tests;
- evidence;
- remaining gate;
- base/head revision.

Issues continue to use explicit acceptance evidence and closure rules.

This system adds machine enforcement; it does not replace those human-readable contracts.

## 10. Local commands

From either repository:

```text
python tools/repository_hygiene.py --changed-from <base-sha> --format-check --strict
python tools/code_documentation_sync.py --changed-from <base-sha> --strict
```

For a repository-wide audit:

```text
python tools/repository_hygiene.py --all --report .runtime/hygiene.json
python tools/code_documentation_sync.py --all --report .runtime/code-doc-sync.json
```

The formatter versions are pinned in the canonical contract. Use the exact versions in CI rather than unpinned `latest` downloads.

## 11. Exceptions

A formatter or synchronization exception must be narrowly scoped and documented.

Acceptable reasons include:

- generated file with a deterministic producer;
- third-party fixture intentionally preserving source formatting;
- syntax that a configured formatter cannot represent without semantic change;
- historical evidence whose formatting must remain unchanged for provenance.

Exceptions must live in the contract or map, not in undocumented local habits.

## 12. Completion condition

The hygiene/synchronization system is considered installed when:

- both repositories carry the same format contract;
- both repositories validate the same universal hygiene rules;
- changed-file formatting is CI-gated;
- code-documentation coupling is CI-gated;
- Foundation runs a read-only family parity audit;
- the existing Family Synchronization Standard remains the higher-level ownership/evidence contract;
- existing documentation debt is measurable and can be reduced without creating a mass unrelated diff.

## References

- Prettier configuration and CLI documentation: repository-local configuration, `--check`, and ignore files. citeturn133518search0turn133518search1turn133518search5
- Ruff formatter/linter documentation: `ruff format --check` and `ruff check`. citeturn622704search0turn622704search3
- markdownlint-cli2 documentation: configuration-based Markdown linting and CI/pre-commit integration. citeturn880103search0
- GitHub CODEOWNERS documentation: code ownership can be defined in `.github/CODEOWNERS` and can be enforced through protected-branch review rules. citeturn752774search0
- GitHub Actions path filters: changes can be scoped to selected paths, with path filtering evaluated alongside branch filters. citeturn752774search1
