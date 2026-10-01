#!/usr/bin/env bash
set -euo pipefail

# Canonical release entrypoint. Keep phase files sourced so the original shell
# variable/trap/exit semantics remain one transaction while responsibilities
# stay separately reviewable and below the monolith threshold.
RELEASE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/release" >/dev/null 2>&1 && pwd)"
source "$RELEASE_DIR/production_release_preflight.sh"
source "$RELEASE_DIR/production_release_deploy_acceptance.sh"
