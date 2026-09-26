# GitHub Actions boundary — public actions, private source only
Updated: 2026-09-26

Foundation workflows must execute only public GitHub actions. They must not execute an action stored inside Z-Solo-King/operations.

Private Operations appears in some workflows because source checkout and action execution are different things. A public actions/checkout action can read a private Operations repository when supplied a narrowly scoped GitHub App installation token. That does not make actions/checkout a private action and does not execute private Operations code as a GitHub Action.

Required implementation for private Operations source:
- public, SHA-pinned actions/checkout;
- short-lived GitHub App installation token with read-only contents permission;
- immutable 40-character Operations commit SHA for runtime evidence;
- resolved SHA verification;
- never use uses: Z-Solo-King/operations/...@...;
- never use a private reusable workflow from Operations.

The workflow policy test rejects private/local repository action references and requires public checkout/script actions when Operations source is used.
