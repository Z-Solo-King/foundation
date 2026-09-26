# Security Policy

## Reporting

Do not publish security-sensitive findings in a public GitHub issue.

Use GitHub's private vulnerability reporting / Security Advisory mechanism
for this repository when it is available. Include the affected revision,
component, reproduction steps, and impact without including live credentials.

## Public/private boundary

This repository is public by design. Public visibility is not a substitute for
secrecy.

Keep credentials, private runtime state, private datasets or holdouts, private
prompts, retailer-specific extraction intelligence, and other non-public
implementation in the private Operations boundary or external secret stores.

## Disclosure rule

Never commit:
- API keys, passwords, bearer tokens, private keys, or session credentials;
- production secret values or secret-bearing exports;
- private manifests, customer data, or evaluation holdouts.

Repository history is durable. Removing a secret from the current tree does
not erase exposure from earlier commits, so suspected credential leaks must be
rotated/revoked immediately.