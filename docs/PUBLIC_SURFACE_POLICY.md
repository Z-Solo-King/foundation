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