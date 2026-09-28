# Documentation Hygiene

**Scope:** `foundation` public repository
**Status:** normative, current

## Canonical sources

- `docs/DOCUMENTATION_INDEX.md` is the documentation index.
- `REPOSITORY_MAP.json` describes ownership and canonical modules.
- `DEPLOYMENT.md` and `.github/workflows/heroic-ai-production-release.yml` describe the public deployment path.
- `docs/FAMILY_CONTRACT.json` and `docs/FAMILY_ARCHITECTURE.md` define the family boundary.
- Live repository state and fresh execution evidence override dated handoffs, old pull requests and chat notes.

## Naming and folders

- Active canonical documents use stable descriptive names without date/revision suffixes.
- Dated snapshots are historical and should live under `docs/history/<topic>/` when relocation is practical.
- New collection folders use lowercase descriptive names; avoid `latest`, `new`, `temp`, `draft` and similar vague names for canonical documents.
- Machine-readable contracts use stable purpose-based names; date suffixes are reserved for historical snapshots.

## Dated documents

Dated documents are retained for provenance, incident history or design history. They must state whether they are historical or current. Historical documents must not imply current production certification.

## Evidence language

Use precise states such as `implemented`, `tested`, `merged`, `deployment-attempted`, `runtime-verified`, `blocked` and `historical`. Do not use `production-ready`, `verified` or `complete` when the available evidence proves only source-level behavior.

## Deployment claims

Never record production success without execution evidence tied to the deployed revision. A secret, workflow file or deployment script is not deployment evidence.

## Repository boundary

Public documentation must not disclose private credentials, private control-plane internals or protected runtime policy values. Describe protected mechanisms at the contract and boundary level.

## Maintenance

When a contract, workflow owner, repository boundary or production gate changes, update the affected canonical document in the same change set. Do not create a new dated plan when an existing canonical document can be corrected.
