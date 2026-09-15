# AI navigation metadata validation

`tools/validate_ai_navigation.py` validates the repository-facing paths in `AI_CODEMAP.json` and `AI_NAVIGATION_INDEX.json`. Cross-repository Operations references are explicit and are not treated as local Foundation files.

The public deployment owner is `.github/workflows/codeql.yml`, which contains the production Worker deployment job after the required public test gate. A standalone `deploy-public-worker.yml` path must not be referenced as the deployment owner.
