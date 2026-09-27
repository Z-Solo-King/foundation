# Public Surface Policy

Foundation is a public repository. The goal is not to hide every implementation
detail; the goal is to expose stable public contracts while keeping
differentiating private control-plane logic outside the public tree.

## Public

Appropriate for Foundation:

- public API/request and response contracts;
- deterministic, credential-free normalization and evidence primitives;
- generic edge/runtime adapters required by the public product boundary;
- public frontend code;
- deterministic public tests and non-sensitive benchmark fixtures;
- sanitized documentation explaining contracts and externally observable behavior.

## Private

Keep in Operations or another private control surface:

- provider credentials, secret-fan-out logic, secret values and credential stores;
- private orchestration and runtime state;
- provider billing/quota decisions and protected resource governance;
- retailer-specific extraction selectors, manifests, target inventories and
  acquisition intelligence;
- private prompts, hidden evaluation sets and unpublished benchmark cases;
- customer/user-private data;
- internal incident timelines and detailed operational state that is not needed
  to explain the public contract.

## Repository rules

1. Public code must not require a secret to understand or test its deterministic contract.
2. Public runtime inputs may select work, but must not bypass authorization, resource,
   policy, provenance or deployment authorities.
3. Private data should cross the public/private boundary only through an explicit,
   versioned contract with least-privilege authentication.
4. Generated operational state is evidence/output, not a source of truth for future behavior.
5. Exact production revisions may remain public when reproducibility requires them,
   but they should have one canonical owner instead of being repeated across many historical snapshots.
6. Commit and PR messages are part of the public surface. Do not put private repository names,
   private URLs, internal credentials, customer details, unpublished tuning data or private workflow
   instructions into them.

## Preferred architecture

Public Foundation -> stable contract / deterministic public boundary
Private Operations -> orchestration / policy / providers / protected runtime
External secret stores -> credentials and other secret material

The split should reduce exposed intellectual property without creating a second runtime,
deployment or policy authority.
## 2026-09-27 public-surface audit hardening

The public disclosure scan is recursive over the public documentation surface rather than a fixed hand-picked file list. It covers root public docs plus every Markdown/JSON file under `docs/`, and PR title/body/commit metadata.

The scanner fail-closes on live Cloudflare identifiers, Worker origins, privileged account-role disclosures, private Operations deployment provenance, live D1 identifiers/counts, version/deployment IDs, credential material and live feed-target URLs.

Live retailer target registries and feed-recovery tooling do not belong in Foundation. The #1103 remediation moves those assets to the private Operations repository and removes the public copies.

Runtime state is documented only at the level required to explain the public contract. Historical live identifiers are redacted even when they were previously observed.

GitHub's current security guidance supports this boundary: secret scanning detects hardcoded credentials across repository history, and push protection is designed to block supported secrets before they reach the repository. Real exposed credentials still require rotation/revocation and history remediation; redaction of non-secret infrastructure metadata is a separate information-disclosure control. 
