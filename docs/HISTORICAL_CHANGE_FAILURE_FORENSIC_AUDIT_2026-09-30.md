# Historical Change / Failure Forensic Audit — 2026-09-30

## Purpose

This is a process and control audit, not a mechanical cleanup pass. It examines closed issues, closed pull requests, current workflow definitions, and representative Actions failures to identify recurrence mechanisms and prevent them.

## Coverage

Repository history:
- Foundation: 249 closed issues, 1,306 closed PRs.
- Operations: 329 closed issues, 1,027 closed PRs.
- Foundation: 43 current workflow definitions inventoried.

Action coverage:
- Foundation has a much larger Actions history than the connected API can safely enumerate as a complete event-by-event replay. The current run API exposes a 40,000-run ceiling/window, while the failed/cancelled result sets are also capped.
- Therefore this audit claims 100% coverage of the current workflow control surface and 100% coverage of the paginated closed issue/PR populations, but not a literal replay of every historical Actions event.

## Executive finding

The recurring defect was a control-system problem:

documented architecture -> ambiguous execution surface -> wrong action/workflow -> late validation -> corrective PR -> stale revision or snapshot -> another failure.

The project usually discovered the local code defect correctly. The slow part was repeatedly rediscovering the correct ownership, revision, evidence class, and workflow route.

## Root causes

### Authority was selected before enforcement

The feed-recovery history is the clearest example. The intended model was public Foundation orchestration with public retailer acquisition, while private Operations retained private intelligence and runtime authority. The historical record still needed an explicit corrective change to restore GitHub Actions ownership to Foundation.

The rule must therefore be executable:

Task -> authority class -> repository -> allowed workflow -> credentials -> evidence tier -> implementation.

A written rule that is not checked at the workflow boundary is guidance, not enforcement.

### Public and private workflow boundaries were partly conventional

Foundation is public. Operations is private. Public PRs, commits, Action history and Action logs therefore form part of the public surface.

The safe model is:
- public Foundation: contracts, deterministic public code, public-safe workflows, sanitized methodology;
- private Operations: protected runtime, private intelligence, private registries, provider details, hidden evaluation data and internal incident state.

A public PR must never be used as a transport mechanism for private implementation detail.

### Stale revisions multiplied failures

Several historical repairs were followed by pin/snapshot/freshness repairs because different workflows were still operating on different immutable revisions.

A revision mismatch is therefore a correctness failure, not merely a documentation issue.

### Evidence classes were repeatedly mixed

Repeated historical mistakes included:
- runner/provisioning failure treated as code failure;
- blocked retailer transport treated as source absence;
- structural CI treated as runtime proof;
- generic provider text treated as research-contract success;
- search-tool negative result treated as repository absence;
- reference/candidate parity treated as correctness even when the reference and candidate shared the same bug.

Correct order:
observation -> classification -> corroboration -> runtime receipt -> acceptance.

Lower-tier evidence cannot satisfy a higher-tier acceptance requirement.

### Change churn amplified elapsed time

Many short-lived branches and replacement PRs meant fixes were often applied to a moving target. The result was serial correction of adjacent contracts rather than one coherent change against one frozen authority.

The prevention is not fewer checks. It is an earlier route decision and a single change-intent record.

## Feed-specific recurrence

The feed history contains all of these patterns in one area:

- multiple feed-hunt implementations;
- private/public ownership corrections;
- stale or conflicting feed discovery paths;
- repeated transport failures that did not always represent extractor defects;
- recovery logic being copied and then re-unified;
- repeated Action attempts before the workflow boundary was made explicit.

The key policy is:

Feed discovery is Foundation-owned public acquisition.

Operations may own private feed intelligence, private target registries, extractor internals and runtime governance. That does not make Operations the workflow executor for public feed discovery.

A feed-discovery workflow must not silently acquire a private Actions dependency.

A private-registry feed job is a separate authority class and must be explicitly classified as such.

## Why it took so long

The evidence indicates that the main latency multipliers were:

1. authority selection was a convention before it was a machine gate;
2. workflow YAML was allowed to encode behavior independently of the prose rule;
3. exact revisions were distributed across many pins and snapshots;
4. CI, runtime, transport and evidence failures were different classes but were investigated serially;
5. tool failures and search limitations sometimes became false negative conclusions;
6. migration parity could pass while preserving a defect from the reference;
7. public/private concerns were sometimes repaired after implementation rather than before execution.

## Prevention controls

### 1. Workflow authority registry

Every workflow is scanned.

A workflow using secrets, a GitHub App token, or private Operations is considered privileged and must be explicitly registered.

An unregistered privileged workflow fails policy validation.

### 2. Public feed boundary

Registered public feed workflows must be credential-free and private-Operations-free.

This prevents the exact recurrence where public feed work drifts into a private Action route.

### 3. Privileged trigger boundary

Privileged workflows must not run on pull_request, pull_request_target, or merge_group. Privileged workflow_run chains must use an explicitly registered trusted upstream workflow.

Privileged push execution must be restricted to main.

This prevents a public PR branch from changing the workflow definition that has access to private credentials.

### 4. Exact revision requirement

Acceptance workflows record the exact Foundation revision and, where applicable, the exact Operations revision.

Snapshots are evidence, not authority.

### 5. Evidence-tier declaration

Every acceptance-critical workflow identifies its evidence tier and its closure requirement.

No benchmark, static audit, or search result can silently upgrade itself into runtime acceptance.

### 6. Failure classification

Failures must preserve a distinction between:
- code defect;
- workflow defect;
- runner/provisioning defect;
- transport restriction;
- provider rejection;
- evidence/artifact defect;
- stale revision;
- policy/authority violation.

This prevents repeated fixes against the wrong layer.

### 7. Route before repair

Before modifying code, the agent must identify:
- owning repository;
- owning component;
- approved workflow;
- public/private classification;
- required credentials;
- exact revision;
- acceptance artifact.

Only then should mechanical work begin.

## Public/private PR policy

Foundation PRs are public by design and therefore should contain only public-safe material.

Operations PRs remain private for protected implementation and internal evidence.

A private issue/PR identifier or detailed internal incident narrative should not be copied into a public Foundation forensic report.

Public Foundation should expose:
- contract IDs;
- sanitized architecture;
- reproducible public behavior;
- public-safe remediation.

Private Operations should retain:
- private target inventories;
- protected runtime implementation;
- internal provider details;
- hidden evaluation data;
- private incident evidence.

This distinction is important because GitHub states that Action history and logs become visible to everyone when a repository is public. GitHub also warns that privileged workflow contexts can expose secrets and should not be combined with execution of untrusted pull-request code. citeturn253140search5turn253140search0

## Existing evidence that supports the prevention model

The saved Master Audit System already defines inventory, six-lane audit, open-issue audit, migration, family ownership, security/trust, reliability/recovery, nightly research, performance, evidence/provenance, peer reconciliation and meta-audit layers. The saved six-lane contract explicitly says audit success is not the same as 100% completion when runtime evidence or scanner errors remain. fileciteturn810file0L1-L1

The current family architecture already defines one-way Foundation -> Operations dependency direction, single-owner rules, credential boundaries, change ordering, and a requirement to update canonical documentation when ownership or policy changes.

The remaining gap was enforcement at the workflow-execution boundary.

## GitHub-specific security finding

The present Foundation workflow surface contains privileged workflows that use private Operations or secrets. Some historical/current review workflows were also PR-triggered.

That combination is unnecessary for private validation and should be eliminated.

GitHub's current guidance says pull_request workflows use reduced trust for forked PRs, but privileged triggers such as pull_request_target and workflow_run require special care; any workflow that has secrets and executes untrusted code can become a supply-chain path. GitHub recommends avoiding privileged PR execution when it is not needed. citeturn253140search0turn253140search8

GitHub also supports explicit workflow-execution policies and environment protections for branch restrictions and secret access. citeturn253140search6turn253140search1

## Outcome of this pass

Completed:
- historical issue/PR population coverage;
- current workflow surface inventory;
- Action failure-pattern analysis;
- feed-specific recurrence reconstruction;
- root-cause model;
- public/private disclosure model;
- machine-enforceable workflow authority policy.

Intentionally not done:
- bulk mechanical cleanup;
- mass branch deletion;
- speculative language migration;
- synthetic runtime evidence;
- historical rewriting of public/private repository history.

The correct next implementation unit is the workflow-authority policy gate, followed by splitting any required public PR checks from privileged main/scheduled validation.

