# CI security analysis policy

## Scope
All GitHub Actions workflow files are analyzed by zizmor and the repository is periodically analyzed by OpenSSF Scorecard.

## Severity
These tools are observation/security signals in the first phase. Application correctness, deployment certification, and runtime acceptance remain separate gates.

- Critical/high findings: must receive an explicit remediation or documented allowlist decision before release.
- Medium/low findings: tracked for remediation; they do not silently become a deployment veto.
- Tool/internal failures: fail the security job because the analysis itself is unavailable.

## Security
The analysis jobs use minimum required permissions. They do not print repository secrets. Actions are pinned to immutable commit SHAs.

## Exceptions
Exceptions must name the rule, scope, rationale, owner, and review date in this document or the dedicated tool configuration. A broad wildcard suppression is not allowed.

