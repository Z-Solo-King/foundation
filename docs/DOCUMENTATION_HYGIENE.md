# Documentation Hygiene

**Scope:** `foundation` public repository  
**Status:** normative documentation rule, current 2026-09-16

## Canonical-source rules

- `docs/DOCUMENTATION_INDEX.md` is the navigation source.
- `DEPLOYMENT.md` and `.github/workflows/codeql.yml` are the source for public deployment mechanics.
- `docs/FAMILY_CONTRACT.json` and `docs/FAMILY_ARCHITECTURE.md` define public/private ownership.
- `AI_CODEMAP.json` defines machine-readable ownership and canonical modules.
- Live repository state and fresh runtime evidence override dated handoffs, continuity notes, old PR descriptions and chat transcripts.

## Dated documents

Dated documents are retained for provenance, incident history, or design history. They must clearly state whether they are historical or current. A historical document must not use present-tense language that implies current production certification.

## Status-language rules

Use precise labels such as `implemented`, `tested`, `merged`, `deployment-attempted`, `runtime-verified`, `blocked`, or `historical`. Do not use `production-ready`, `verified`, or `complete` when the evidence only proves source-level behavior.

## Deployment claims

Never record a production success without execution evidence tied to the deployed revision. Secret availability, workflow source, or existence of a deployment script is not deployment evidence.

## Repository-boundary rules

Public documentation must not disclose private credentials, private control-plane internals, or protected runtime policy values. Describe protected mechanisms at the contract/boundary level only.

## Maintenance rule

When a canonical contract, workflow owner, repository boundary, or production gate changes, update the canonical document and this hygiene policy in the same change set when the rule itself changes. Avoid creating a new dated plan for a correction that belongs in an existing canonical document.
