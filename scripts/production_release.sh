#!/usr/bin/env bash
set -euo pipefail

OPERATIONS_REPOSITORY="Z-Solo-King/operations"
OPERATIONS_REF="122a334d85708e2e42db59b74114d1396ca98f31"
OPERATIONS_SERVICE_NAME="operations"
BASE_URL="https://ai-cio.pages.dev"
ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${GITHUB_RUN_ATTEMPT:-1}"

cleanup() {
  rm -rf "$RUNNER_TEMP/operations" "$RUNNER_TEMP/operations-secrets.env" "$RUNNER_TEMP/public-secrets.env" \
    "$RUNNER_TEMP/git-askpass-operations.sh" "$RUNNER_TEMP/operations-app.pem" \
    "$RUNNER_TEMP/github-app-jwt.txt" "$RUNNER_TEMP/github-app-installation.json" \
    "$RUNNER_TEMP/github-app-installation-meta.json" wrangler.production.generated.toml health.json readiness.json frontend.html \
    /tmp/styles.css /tmp/app.js /tmp/composer.js /tmp/lifecycle_controller.js
}
trap cleanup EXIT

test -n "${CLOUDFLARE_API_TOKEN:-}" || { echo 'Missing CLOUDFLARE_API_TOKEN GitHub secret'; exit 1; }
test -n "${CLOUDFLARE_ACCOUNT_ID:-}" || { echo 'Missing CLOUDFLARE_ACCOUNT_ID GitHub secret'; exit 1; }
test -n "${OPERATIONS_APP_ID:-}" || { echo 'Missing OPERATIONS_APP_ID GitHub Actions secret'; exit 1; }
test -n "${OPERATIONS_APP_PRIVATE_KEY:-}" || { echo 'Missing OPERATIONS_APP_PRIVATE_KEY GitHub Actions secret'; exit 1; }
test -n "${AUTH_TOKEN:-}" || { echo 'Missing AUTH_TOKEN GitHub Actions secret'; exit 1; }
test -n "${B2_KEY_ID:-}" || { echo 'Missing B2_KEY_ID GitHub Actions secret'; exit 1; }
test -n "${B2_APPLICATION_KEY:-}" || { echo 'Missing B2_APPLICATION_KEY GitHub Actions secret'; exit 1; }
test "$OPERATIONS_REF" = '122a334d85708e2e42db59b74114d1396ca98f31'

after_install_marker=''

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio coverage workers-py workers-runtime-sdk uv
uv --version
python -m compileall -q backend foundation_core worker.py
python -c "import foundation_core; print(foundation_core.__all__)"
coverage run --branch --source=backend,foundation_core,worker --omit='tests/*' -m pytest tests/ -v
coverage report --show-missing --fail-under=100 --omit='tests/*'
python -m benchmark.chatbot_query_benchmark --input benchmark/chatbot-query-corpus.json --output .runtime/chatbot-query-benchmark.json
python -m pytest -q tests/test_workflow_policy.py
python scripts/public_security_lint.py --strict

test ! -e backend/learning/promotion.py
# The public Worker intentionally references the abstract OPERATIONS service binding.
# Scan production source for private implementation markers and concrete private
# service topology instead of the generic binding identifier.
! grep -RniE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' foundation_core backend wrangler.toml migrations
! grep -nE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' worker.py
! grep -RniE 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY|github_pat_[A-Za-z0-9_]+' foundation_core backend worker.py wrangler.toml migrations tests

token_verify_status=$(curl -sS -o "$RUNNER_TEMP/cloudflare-token-verify.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' \
  https://api.cloudflare.com/client/v4/user/tokens/verify || true)
if [ "$token_verify_status" != '200' ] || ! jq -e '.success == true and .result.status == "active"' "$RUNNER_TEMP/cloudflare-token-verify.json" >/dev/null 2>&1; then
  echo "Cloudflare token self-verify endpoint was not usable (HTTP $token_verify_status); continuing with account-scoped authorization check."
  jq -c '{success,message,result:{status:(.result.status // null),id:(.result.id // null)}}' "$RUNNER_TEMP/cloudflare-token-verify.json" 2>/dev/null || true
fi

databases_status=$(curl -sS -o "$RUNNER_TEMP/cloudflare-d1-databases.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/d1/database" || true)
test "$databases_status" = '200' || {
  echo "Cloudflare D1 authorization check failed: HTTP $databases_status"
  jq -c '{success,message,errors}' "$RUNNER_TEMP/cloudflare-d1-databases.json" 2>/dev/null || cat "$RUNNER_TEMP/cloudflare-d1-databases.json"
  exit 1
}
databases=$(cat "$RUNNER_TEMP/cloudflare-d1-databases.json")
database_id=$(jq -r '[.result[]? | select(.name == "research-intelligence") | .uuid] | if length == 1 then .[0] else empty end' <<<"$databases")
test -n "$database_id" || { echo 'Expected exactly one research-intelligence D1 database'; exit 1; }
echo "Cloudflare account/D1 authorization: PASS ($database_id)"

# Preflight and stage the private Operations handoff before touching production.
key_file="$RUNNER_TEMP/operations-app.pem"
umask 077
printf '%s\n' "$OPERATIONS_APP_PRIVATE_KEY" > "$key_file"
chmod 600 "$key_file"
python - "$OPERATIONS_APP_ID" "$key_file" > "$RUNNER_TEMP/github-app-jwt.txt" <<'PY'
import base64
import json
import subprocess
import sys
import time

app_id, key_file = sys.argv[1:]
def b64url(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode('ascii')
now = int(time.time())
header = {"alg": "RS256", "typ": "JWT"}
payload = {"iat": now - 60, "exp": now + 540, "iss": app_id}
unsigned = f"{b64url(json.dumps(header, separators=(',', ':')).encode())}.{b64url(json.dumps(payload, separators=(',', ':')).encode())}".encode()
proc = subprocess.run(["openssl", "dgst", "-sha256", "-sign", key_file], input=unsigned, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
print(unsigned.decode() + "." + b64url(proc.stdout))
PY
app_jwt=$(cat "$RUNNER_TEMP/github-app-jwt.txt")

# Resolve the current installation dynamically; do not depend on a stored installation-id secret.
installation_output="$RUNNER_TEMP/github-app-installation-discovery.txt"
installation_error="$RUNNER_TEMP/github-app-installation-discovery.err"
set +e
OPERATIONS_APP_JWT="$app_jwt" python scripts/resolve_operations_installation.py >"$installation_output" 2>"$installation_error"
installation_status=$?
set -e
if [ "$installation_status" -ne 0 ]; then
  echo "GitHub App installation discovery failed (exit $installation_status)"
  cat "$installation_error" 2>/dev/null || true
  cat "$installation_output" 2>/dev/null || true
  exit 1
fi
installation_id="$(tr -d "\r\n" < "$installation_output")"
test -n "$installation_id" || { echo "GitHub App installation discovery returned an empty installation id"; exit 1; }
echo "Resolved Operations GitHub App installation: PASS ($installation_id)"

# Verify that the resolved installation belongs to the supplied App, and mint a short-lived token.
installation_meta_status=$(curl -sS -o "$RUNNER_TEMP/github-app-installation-meta.json" -w '%{http_code}' \
  -H 'Accept: application/vnd.github+json' \
  -H "Authorization: Bearer ${app_jwt}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/app/installations/${installation_id}")
echo "GET GitHub App installation metadata -> HTTP ${installation_meta_status}"
if [ "$installation_meta_status" != '200' ]; then
  jq -c '{message,errors,documentation_url}' "$RUNNER_TEMP/github-app-installation-meta.json" || cat "$RUNNER_TEMP/github-app-installation-meta.json"
  exit 1
fi

installation_response_status=$(curl -sS -o "$RUNNER_TEMP/github-app-installation.json" -w '%{http_code}' \
  -X POST \
  -H 'Accept: application/vnd.github+json' \
  -H "Authorization: Bearer ${app_jwt}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/app/installations/${installation_id}/access_tokens")
echo "POST GitHub App installation token -> HTTP ${installation_response_status}"
if [ "$installation_response_status" != '201' ]; then
  jq -c '{message,errors,documentation_url}' "$RUNNER_TEMP/github-app-installation.json" || cat "$RUNNER_TEMP/github-app-installation.json"
  exit 1
fi

github_app_token=$(python - "$RUNNER_TEMP/github-app-installation.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['token'])
PY
)
test -n "$github_app_token"
echo "::add-mask::$github_app_token"

repo_status=$(curl -sS -o "$RUNNER_TEMP/operations-repo-response.json" -w '%{http_code}' \
  -H 'Accept: application/vnd.github+json' -H "Authorization: Bearer ${github_app_token}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' "https://api.github.com/repos/${OPERATIONS_REPOSITORY}")
echo "GET Operations repository -> HTTP ${repo_status}"
test "$repo_status" = '200' || { jq -c '{message,errors,documentation_url}' "$RUNNER_TEMP/operations-repo-response.json" || cat "$RUNNER_TEMP/operations-repo-response.json"; exit 1; }
jq -e --arg repo "$OPERATIONS_REPOSITORY" '.full_name == $repo and .private == true' "$RUNNER_TEMP/operations-repo-response.json" >/dev/null

ref_status=$(curl -sS -o "$RUNNER_TEMP/operations-ref-response.json" -w '%{http_code}' \
  -H 'Accept: application/vnd.github+json' -H "Authorization: Bearer ${github_app_token}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' "https://api.github.com/repos/${OPERATIONS_REPOSITORY}/git/commits/${OPERATIONS_REF}")
echo "GET Operations approved commit -> HTTP ${ref_status}"
test "$ref_status" = '200' || { jq -c '{message,errors,documentation_url}' "$RUNNER_TEMP/operations-ref-response.json" || cat "$RUNNER_TEMP/operations-ref-response.json"; exit 1; }
jq -e --arg expected "$OPERATIONS_REF" '.sha == $expected' "$RUNNER_TEMP/operations-ref-response.json" >/dev/null

echo "private Operations access: PASS (${OPERATIONS_REF})"

# The canonical public origin is the Pages front door; no custom-domain zone is required for this release.
askpass="$RUNNER_TEMP/git-askpass-operations.sh"
cat > "$askpass" <<'EOF'
#!/bin/sh
case "$1" in
  *Username*) printf '%s\n' x-access-token ;;
  *Password*) printf '%s\n' "$GITHUB_APP_TOKEN" ;;
  *) printf '%s\n' '' ;;
esac
EOF
chmod 700 "$askpass"
export GITHUB_APP_TOKEN="$github_app_token"
export GIT_ASKPASS="$askpass"
export GIT_TERMINAL_PROMPT=0
rm -rf "$RUNNER_TEMP/operations"
git clone --no-checkout "https://github.com/${OPERATIONS_REPOSITORY}.git" "$RUNNER_TEMP/operations"
git -C "$RUNNER_TEMP/operations" fetch --no-tags origin "$OPERATIONS_REF"
git -C "$RUNNER_TEMP/operations" checkout --detach "$OPERATIONS_REF"
test "$(git -C "$RUNNER_TEMP/operations" rev-parse HEAD)" = "$OPERATIONS_REF"

# The production code remains pinned to the approved immutable revision, while the
# family semantic audit must consume the latest synchronized family-state snapshot.
# Keep full commit ancestry so `main...HEAD` resolves to the real merge base instead
# of turning --new-only into a whole-tree scan because the immutable pin was shallow.
git -C "$RUNNER_TEMP/operations" fetch --no-tags origin main
git -C "$RUNNER_TEMP/operations" branch --force main origin/main
test "$(git -C "$RUNNER_TEMP/operations" rev-parse main)" = "$(git -C "$RUNNER_TEMP/operations" rev-parse origin/main)"
operations_merge_base="$(git -C "$RUNNER_TEMP/operations" merge-base main HEAD)"
test -n "$operations_merge_base"
echo "Operations architecture diff base: ${operations_merge_base}"
git -C "$RUNNER_TEMP/operations" show "origin/main:docs/FAMILY_SYNC_STATE.json" > "$RUNNER_TEMP/operations/docs/FAMILY_SYNC_STATE.json"
# The immutable runtime pin is preserved, while synchronized family navigation is overlaid from Operations main.
git -C "$RUNNER_TEMP/operations" show "origin/main:docs/AI_ANALYSIS_MAP.md" > "$RUNNER_TEMP/operations/docs/AI_ANALYSIS_MAP.md"
jq -e '
  if (.repositories? != null) then
    (.repositories.foundation.last_audited_main_sha | type == "string" and length == 40)
    and (.repositories.operations.last_audited_main_sha | type == "string" and length == 40)
  elif (.live_main? != null) then
    (.live_main.foundation | type == "string" and length == 40)
    and (.live_main.operations | type == "string" and length == 40)
  else
    false
  end
' "$RUNNER_TEMP/operations/docs/FAMILY_SYNC_STATE.json" >/dev/null
echo "Family sync snapshot refresh: PASS (Operations main state overlaid; runtime remains ${OPERATIONS_REF})"

# Fail closed if the promoted Operations pin does not contain the canonical
# authenticated chatbot backend boundary and zero-cost Workers AI provider contract.
grep -q '^CHAT_LLM_PROVIDERS = "cloudflare_workers_ai"$' "$RUNNER_TEMP/operations/wrangler.toml"
grep -q '^CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/zai-org/glm-4.7-flash"$' "$RUNNER_TEMP/operations/wrangler.toml"
grep -q '"workers_ai_neurons":10000' "$RUNNER_TEMP/operations/wrangler.toml"
grep -q 'CHAT_BACKEND_TOKEN' "$RUNNER_TEMP/operations/worker.py"

# Fail before deployment if the pinned Operations tree contains any Python syntax error.
python -m compileall -q "$RUNNER_TEMP/operations"

# Run the bounded cross-repository audit before touching production. This is evidence
# collection inside the canonical production owner, not a second deployment authority.
mkdir -p .runtime
python "$RUNNER_TEMP/operations/scripts/run_cross_repo_audit.py" \
  "$GITHUB_WORKSPACE" "$RUNNER_TEMP/operations" \
  --output "$RUNNER_TEMP/cross-repository-audit-receipt.json"
test -s "$RUNNER_TEMP/cross-repository-audit-receipt.json"
jq -e '.schema == "cross-repository-audit-receipt/v1" and .passed == true' \
  "$RUNNER_TEMP/cross-repository-audit-receipt.json" >/dev/null
cp "$RUNNER_TEMP/cross-repository-audit-receipt.json" .runtime/cross-repository-audit-receipt.json
echo "Cross-repository audit acceptance: PASS"

# Materialize the pinned public Foundation deterministic core locally.
# Cloudflare Python Workers must bundle local Worker-compatible modules rather
# than resolve a Git URL package during the Worker build.
python "$RUNNER_TEMP/operations/scripts/sync_public_core.py"
test -f "$RUNNER_TEMP/operations/foundation_core/__init__.py"


printf '%s\n' \
  'name = "heroic"' \
  'main = "worker.py"' \
  'compatibility_date = "2026-09-09"' \
  'compatibility_flags = ["python_workers", "enable_request_signal", "request_signal_passthrough"]' \
  'workers_dev = true' \
  'preview_urls = false' \
  '' \
  '[assets]' \
  'directory = "./frontend"' \
  'binding = "ASSETS"' \
  'not_found_handling = "single-page-application"' \
  '' \
  '[[d1_databases]]' \
  'binding = "DB"' \
  'database_name = "research-intelligence"' \
  "database_id = \"${database_id}\"" \
  '' \
  '[[services]]' \
  'binding = "OPERATIONS"' \
  "service = \"${OPERATIONS_SERVICE_NAME}\"" \
  '' \
  '[secrets]' \
  'required = ["AUTH_TOKEN", "B2_KEY_ID", "B2_APPLICATION_KEY"]' \
  '' \
  '[vars]' \
  'ENVIRONMENT = "production"' \
  'STRICT_ZERO_COST_ONLY = "true"' \
  "RELEASE_FOUNDATION_SHA = \"${GITHUB_SHA}\"" \
  "RELEASE_OPERATIONS_REF = \"${OPERATIONS_REF}\"" \
  'B2_BUCKET = "SoloKing"' \
  'B2_ENDPOINT = "https://s3.eu-central-003.backblazeb2.com"' \
  > wrangler.production.generated.toml

grep -q '^database_name = "research-intelligence"$' wrangler.production.generated.toml
grep -q '^directory = "./frontend"$' wrangler.production.generated.toml
grep -q '^binding = "ASSETS"$' wrangler.production.generated.toml
grep -q "^service = \"${OPERATIONS_SERVICE_NAME}\"$" wrangler.production.generated.toml

public_secret_file="$RUNNER_TEMP/public-secrets.env"
printf 'AUTH_TOKEN=%s\nB2_KEY_ID=%s\nB2_APPLICATION_KEY=%s\n' "$AUTH_TOKEN" "$B2_KEY_ID" "$B2_APPLICATION_KEY" > "$public_secret_file"
chmod 600 "$public_secret_file"

# Rename-safe Cloudflare deployment sequence.
# Foundation and Operations have reciprocal Service Bindings. Cloudflare requires the
# target Worker to exist before deploying the caller, so first create the Operations
# Worker without its reciprocal Foundation binding. Then deploy Foundation -> Operations,
# and finally redeploy Operations with its canonical Foundation binding.
persistence_seed_file="$RUNNER_TEMP/persistence-rollover-seed.json"
persistence_seed_payload='{"operation":"persistence_seed"}'
legacy_public_worker="${LEGACY_PUBLIC_WORKER:-}"
legacy_private_worker="${LEGACY_PRIVATE_WORKER:-}"
test -n "$legacy_public_worker" || { echo 'Missing LEGACY_PUBLIC_WORKER migration input'; exit 1; }
test -n "$legacy_private_worker" || { echo 'Missing LEGACY_PRIVATE_WORKER migration input'; exit 1; }
secret_file="$RUNNER_TEMP/operations-secrets.env"
printf 'AUTH_TOKEN=%s\nCHAT_BACKEND_TOKEN=%s\n' "$AUTH_TOKEN" "$AUTH_TOKEN" > "$secret_file"
chmod 600 "$secret_file"
bootstrap_config="$RUNNER_TEMP/operations/wrangler.bootstrap.toml"
cp "$RUNNER_TEMP/operations/wrangler.toml" "$bootstrap_config"
python - "$bootstrap_config" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)
output = []
skip = False
removed = 0
for line in lines:
    stripped = line.strip()
    if stripped == "[[services]]":
        skip = True
        removed += 1
        continue
    if skip and stripped.startswith("[["):
        skip = False
    if not skip:
        output.append(line)
if removed != 1 or skip:
    raise SystemExit(f"expected exactly one complete Operations services block, removed={removed}, trailing_skip={skip}")
path.write_text("".join(output), encoding="utf-8")
PY
! grep -q '^\[\[services\]\]$' "$bootstrap_config"
! grep -q '^service = "heroic"$' "$bootstrap_config"

# Always bootstrap the Operations target without its reciprocal Foundation binding.
# Cloudflare service-binding deployment fails closed when the target Worker is absent;
# making this idempotent removes the unreliable existence-probe dependency.
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config "$bootstrap_config" --secrets-file "$secret_file" --message "github:${OPERATIONS_REF}" --tag "github:${OPERATIONS_REF}:bootstrap-${ACCEPTANCE_RUN_ID}")
echo "Operations binding-free bootstrap deployment: PASS"



npx --yes wrangler@4.131.1 d1 migrations apply research-intelligence --remote --config wrangler.production.generated.toml
pywrangler deploy --config wrangler.production.generated.toml --secrets-file "$public_secret_file" --message "github:${GITHUB_SHA}"

health_status=$(curl -sS -o health.json -w '%{http_code}' "$BASE_URL/health")
echo "GET /health -> HTTP ${health_status}"
cat health.json
test "$health_status" = '200'
jq -e '.ok == true and .environment == "production"' health.json >/dev/null

readiness=$(curl -sS -o readiness.json -w '%{http_code}' "$BASE_URL/readiness")
echo "GET /readiness -> HTTP ${readiness}"
cat readiness.json
test "$readiness" = '200'
jq -e '.ready == true and .database == true' readiness.json >/dev/null

ui=$(curl -sS -o frontend.html -w '%{http_code}' "$BASE_URL/")
echo "GET / -> HTTP ${ui}"
test "$ui" = '200'
grep -q '<title>Heroic AI — Chat & Research</title>' frontend.html
test -s frontend.html

for asset in styles.css app.js composer.js lifecycle_controller.js; do
  asset_status=$(curl -sS -o "/tmp/${asset}" -w '%{http_code}' "$BASE_URL/${asset}")
  echo "GET /${asset} -> HTTP ${asset_status}"
  test "$asset_status" = '200'
  test -s "/tmp/${asset}"
done

# Redeploy Operations against the new Foundation Worker, proving the final private binding.
npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote \
  --file="$RUNNER_TEMP/operations/docs/RESOURCE_GOVERNANCE_D1_SCHEMA.sql" \
  --config="$RUNNER_TEMP/operations/wrangler.toml"
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:${OPERATIONS_REF}" --tag "github:${OPERATIONS_REF}:foundation-binding-${ACCEPTANCE_RUN_ID}")

operations_deployments_status=$(curl -sS -o "$RUNNER_TEMP/operations-deployments.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${OPERATIONS_SERVICE_NAME}/deployments" || true)
echo "GET Operations deployments -> HTTP ${operations_deployments_status}"
test "$operations_deployments_status" = "200" || {
  jq -c '{message,errors}' "$RUNNER_TEMP/operations-deployments.json" 2>/dev/null || cat "$RUNNER_TEMP/operations-deployments.json"
  exit 1
}
operations_version_id=$(jq -r '.result.deployments[0].versions[]? | select(.percentage == 100) | .version_id' "$RUNNER_TEMP/operations-deployments.json" | head -n1)
test -n "$operations_version_id" || { echo 'No 100% active Operations Worker version found'; exit 1; }

operations_version_status=$(curl -sS -o "$RUNNER_TEMP/operations-version.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${OPERATIONS_SERVICE_NAME}/versions/${operations_version_id}" || true)
echo "GET Operations active version -> HTTP ${operations_version_status}"
test "$operations_version_status" = "200"
jq -e --arg expected "github:${OPERATIONS_REF}" '((.result.annotations["workers/message"] // "") == $expected) or ((.result.annotations["workers/tag"] // "") == $expected)' "$RUNNER_TEMP/operations-version.json" >/dev/null
echo "Operations Cloudflare provenance: PASS (github:${OPERATIONS_REF})"

# P0 deployment-boundary persistence/replay acceptance on the renamed Worker pair.
persistence_seed_status=$(curl -sS --max-time 30 -o "$persistence_seed_file" -w '%{http_code}' \
  -H "Authorization: Bearer $AUTH_TOKEN" -H 'Content-Type: application/json' \
  -d "$persistence_seed_payload" "$BASE_URL/api/v1/chatbot/diagnostic" || true)
echo "POST persistence_seed -> HTTP $persistence_seed_status"
test "$persistence_seed_status" = "200"
jq -e '.ok == true and (.sentinel_id | type == "string" and length > 0)' "$persistence_seed_file" >/dev/null

chat_rollover_payload=$(jq -nc --arg chat_id "production-chat-rollover-${ACCEPTANCE_RUN_ID}" --arg request_id "production-chat-rollover-request-${ACCEPTANCE_RUN_ID}" '{chat_id:$chat_id,request_id:$request_id,message:"Return one concise sentence explaining why the public Worker uses an authenticated private service binding.",mode:"chat",strict_zero_cost_only:true}')
chat_rollover_key="production-chat-rollover-${ACCEPTANCE_RUN_ID}"
chat_rollover_status=$(curl -sS --max-time 90 -o "$RUNNER_TEMP/chat-rollover-before.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" -H 'Content-Type: application/json' -H "Idempotency-Key: ${chat_rollover_key}" \
  -d "$chat_rollover_payload" "$BASE_URL/api/v1/chat")
echo "POST /api/v1/chat rollover seed -> HTTP ${chat_rollover_status}"
test "$chat_rollover_status" = "200"
jq -e '.ok == true and (.response.result_state == "COMPLETE" or .response.result_state == "PARTIAL") and (.response.response_id | type == "string" and length > 0)' "$RUNNER_TEMP/chat-rollover-before.json" >/dev/null

# Create an additional Operations version, then verify the durable chat/persistence state survives it.
(cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:${OPERATIONS_REF}" --tag "github:${OPERATIONS_REF}:persistence-boundary-${ACCEPTANCE_RUN_ID}")
boundary_deployments_status=$(curl -sS -o "$RUNNER_TEMP/operations-boundary-deployments.json" -w '%{http_code}' -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${OPERATIONS_SERVICE_NAME}/deployments" || true)
test "$boundary_deployments_status" = "200"
boundary_version_id=$(jq -r '.result.deployments[0].versions[]? | select(.percentage == 100) | .version_id' "$RUNNER_TEMP/operations-boundary-deployments.json" | head -n1)
test -n "$boundary_version_id" || { echo 'No active Operations boundary version found'; exit 1; }
echo "Operations version boundary: PASS (${operations_version_id} -> ${boundary_version_id})"
persistence_sentinel_id=$(jq -r '.sentinel_id' "$persistence_seed_file")
persistence_verify_payload=$(jq -nc --arg operation "persistence_verify" --arg sentinel_id "$persistence_sentinel_id" '{operation:$operation,sentinel_id:$sentinel_id}')
persistence_verify_status=$(curl -sS --max-time 30 -o "$RUNNER_TEMP/persistence-rollover-verify.json" -w '%{http_code}' -H "Authorization: Bearer $AUTH_TOKEN" -H 'Content-Type: application/json' -d "$persistence_verify_payload" "$BASE_URL/api/v1/chatbot/diagnostic" || true)
echo "POST persistence_verify -> HTTP ${persistence_verify_status}"
test "$persistence_verify_status" = "200"
jq -e '.ok == true and .memory_persisted_across_version == true and .replay_nonce_rejected_after_version_change == true and .cleanup_status == 200' "$RUNNER_TEMP/persistence-rollover-verify.json" >/dev/null
chat_rollover_after_status=$(curl -sS --max-time 60 -o "$RUNNER_TEMP/chat-rollover-after.json" -w '%{http_code}' -H "Authorization: Bearer ${AUTH_TOKEN}" -H 'Content-Type: application/json' -H "Idempotency-Key: ${chat_rollover_key}" -d "$chat_rollover_payload" "$BASE_URL/api/v1/chat")
echo "POST /api/v1/chat rollover replay -> HTTP ${chat_rollover_after_status}"
test "$chat_rollover_after_status" = "200"
jq -e --arg expected_id "$(jq -r '.response.response_id' "$RUNNER_TEMP/chat-rollover-before.json")" '.ok == true and .response.response_id == $expected_id' "$RUNNER_TEMP/chat-rollover-after.json" >/dev/null
echo "Live chat redeployment replay acceptance: PASS"
cp "$RUNNER_TEMP/persistence-rollover-verify.json" .runtime/persistence-rollover-verify.json
echo "Live memory/replay deployment-boundary acceptance: PASS"# Record the live durable MODEL_CALLS quota state before the required model-generation
# acceptance. This is a bounded non-secret diagnostic: no auth token or provider payload
# is queried, only governance counters from the canonical D1 authority.
npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote \
  --config="$RUNNER_TEMP/operations/wrangler.toml" \
  --command="SELECT scope, window_id, resource_kind, limit_units, reserved_units, consumed_units, updated_at FROM resource_governance_quota WHERE resource_kind = 'model_calls' ORDER BY updated_at DESC LIMIT 5;" \
  --json > "$RUNNER_TEMP/model-call-quota.json"
echo "--- model-call-quota.snapshot ---"
cat "$RUNNER_TEMP/model-call-quota.json"
echo "--- end model-call-quota.snapshot ---"
cp "$RUNNER_TEMP/model-call-quota.json" .runtime/model-call-quota.json

npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote \
  --config="$RUNNER_TEMP/operations/wrangler.toml" \
  --command="SELECT reservation_id, scope, window_id, resource_kind, amount, state, idempotency_key, lease_expires_at, updated_at FROM resource_governance_reservations WHERE resource_kind = 'model_calls' ORDER BY updated_at DESC LIMIT 10;" \
  --json > "$RUNNER_TEMP/model-call-reservations.json"
echo "--- model-call-reservations.snapshot ---"
cat "$RUNNER_TEMP/model-call-reservations.json"
echo "--- end model-call-reservations.snapshot ---"
cp "$RUNNER_TEMP/model-call-reservations.json" .runtime/model-call-reservations.json

# Exercise the real public-to-private conversational and research paths only after
# both Workers are deployed and the private provenance gate has passed.
live_chat_payload=$(jq -nc \
  --arg chat_id "production-live-${ACCEPTANCE_RUN_ID}" \
  --arg request_id "production-chat-${ACCEPTANCE_RUN_ID}" \
  '{chat_id:$chat_id,request_id:$request_id,message:"Give a concise explanation of why authenticated service bindings are used between Foundation and the private control plane.",mode:"chat",strict_zero_cost_only:true,require_model_generation:true}')
live_chat_key="production-chat-${ACCEPTANCE_RUN_ID}"
live_chat_status=$(curl -sS --max-time 90 \
  -o "$RUNNER_TEMP/live-chat.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: ${live_chat_key}" \
  -d "${live_chat_payload}" \
  "${BASE_URL}/api/v1/chat")
echo "POST /api/v1/chat -> HTTP ${live_chat_status}"
if [ "$live_chat_status" != '200' ]; then
  echo '--- live-chat.body ---'
  cat "$RUNNER_TEMP/live-chat.json" || true
  echo '--- end live-chat.body ---'
  exit 1
fi
jq -e '.ok == true and (.response.result_state == "COMPLETE" or .response.result_state == "PARTIAL") and .response.generation_status == "model_generated" and .response.provider == "cloudflare_workers_ai" and ((.response.text // "") | length > 0)' \
  "$RUNNER_TEMP/live-chat.json" >/dev/null
live_chat_state=$(jq -r '.response.result_state' "$RUNNER_TEMP/live-chat.json")
live_chat_generation=$(jq -r '.response.generation_status' "$RUNNER_TEMP/live-chat.json")
echo "Live chat acceptance: PASS (result_state=${live_chat_state}; generation_status=${live_chat_generation})"

live_chat_replay_status=$(curl -sS --max-time 30 \
  -o "$RUNNER_TEMP/live-chat-replay.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: ${live_chat_key}" \
  -d "${live_chat_payload}" \
  "${BASE_URL}/api/v1/chat")
echo "POST /api/v1/chat replay -> HTTP ${live_chat_replay_status}"
test "$live_chat_replay_status" = '200'
jq -e --arg request_id "production-chat-${ACCEPTANCE_RUN_ID}" \
  '.ok == true and .request_id == $request_id and .response.response_id == ("chat-" + $request_id)' \
  "$RUNNER_TEMP/live-chat-replay.json" >/dev/null
echo "Live chat idempotency acceptance: PASS"

# True concurrent P0 duplicate acceptance: both requests must converge on one durable response.
concurrent_chat_payload=$(jq -nc \
  --arg chat_id "production-concurrent-${ACCEPTANCE_RUN_ID}" \
  --arg request_id "production-concurrent-request-${ACCEPTANCE_RUN_ID}" \
  '{chat_id:$chat_id,request_id:$request_id,message:"Return one concise sentence about authenticated service bindings.",mode:"chat",strict_zero_cost_only:true}')
concurrent_chat_key="production-concurrent-${ACCEPTANCE_RUN_ID}"
curl -sS --max-time 90 -o "$RUNNER_TEMP/concurrent-chat-1.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" -H 'Content-Type: application/json' \
  -H "Idempotency-Key: ${concurrent_chat_key}" -d "$concurrent_chat_payload" "$BASE_URL/api/v1/chat" > "$RUNNER_TEMP/concurrent-chat-1.status" &
concurrent_pid_1=$!
curl -sS --max-time 90 -o "$RUNNER_TEMP/concurrent-chat-2.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" -H 'Content-Type: application/json' \
  -H "Idempotency-Key: ${concurrent_chat_key}" -d "$concurrent_chat_payload" "$BASE_URL/api/v1/chat" > "$RUNNER_TEMP/concurrent-chat-2.status" &
concurrent_pid_2=$!
set +e
wait "$concurrent_pid_1"
concurrent_wait_1=$?
wait "$concurrent_pid_2"
concurrent_wait_2=$?
set -e
concurrent_status_1="$(cat "$RUNNER_TEMP/concurrent-chat-1.status" 2>/dev/null || true)"
concurrent_status_2="$(cat "$RUNNER_TEMP/concurrent-chat-2.status" 2>/dev/null || true)"
echo "Concurrent chat curl exit codes: request1=${concurrent_wait_1} request2=${concurrent_wait_2}"
echo "Concurrent chat HTTP statuses: request1=${concurrent_status_1} request2=${concurrent_status_2}"
if [ "$concurrent_wait_1" -ne 0 ] || [ "$concurrent_wait_2" -ne 0 ] || [ "$concurrent_status_1" != '200' ] || [ "$concurrent_status_2" != '200' ]; then
  echo '--- concurrent-chat-1.body ---'
  cat "$RUNNER_TEMP/concurrent-chat-1.json" 2>/dev/null || true
  echo '--- concurrent-chat-2.body ---'
  cat "$RUNNER_TEMP/concurrent-chat-2.json" 2>/dev/null || true
  echo '--- end concurrent chat diagnostics ---'
  exit 1
fi
if ! jq -e --slurpfile second "$RUNNER_TEMP/concurrent-chat-2.json" '.ok == true and .response.response_id == ($second[0].response.response_id) and .response.result_state == ($second[0].response.result_state)' "$RUNNER_TEMP/concurrent-chat-1.json" >/dev/null; then
  echo 'Concurrent chat terminal convergence contract failed:'
  cat "$RUNNER_TEMP/concurrent-chat-1.json" 2>/dev/null || true
  cat "$RUNNER_TEMP/concurrent-chat-2.json" 2>/dev/null || true
  exit 1
fi
echo "Live concurrent chat idempotency acceptance: PASS"

# Explicit governed policy denial must be BLOCKED, not a provider call or a transport error.
policy_block_payload=$(jq -nc \
  --arg chat_id "production-policy-${ACCEPTANCE_RUN_ID}" \
  --arg request_id "production-policy-request-${ACCEPTANCE_RUN_ID}" \
  '{chat_id:$chat_id,request_id:$request_id,message:"https://example.com/",operation:"map",input_records:[{"id":"policy-probe"}],mode:"chat",strict_zero_cost_only:true}')
policy_block_status=$(curl -sS --max-time 30 -o "$RUNNER_TEMP/policy-block.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" -H 'Content-Type: application/json' \
  -H "Idempotency-Key: production-policy-${ACCEPTANCE_RUN_ID}" -d "$policy_block_payload" "$BASE_URL/api/v1/chat")
echo "POST /api/v1/chat policy denial -> HTTP ${policy_block_status}"
if [ "$policy_block_status" != '200' ]; then
  echo '--- policy-block.body ---'
  cat "$RUNNER_TEMP/policy-block.json" || true
  echo '--- end policy-block.body ---'
  exit 1
fi
test "$policy_block_status" = '200'
if ! jq -e '.ok == true and .response.status == "blocked" and .response.result_state == "BLOCKED" and .response.operation == "map"' "$RUNNER_TEMP/policy-block.json" >/dev/null; then
  echo '--- policy-block.body ---'
  cat "$RUNNER_TEMP/policy-block.json" || true
  echo '--- end policy-block.body ---'
  exit 1
fi
echo "Live policy denial acceptance: PASS"

cp "$RUNNER_TEMP/chat-rollover-before.json" .runtime/chat-rollover-before.json
cp "$RUNNER_TEMP/chat-rollover-after.json" .runtime/chat-rollover-after.json
cp "$RUNNER_TEMP/concurrent-chat-1.json" .runtime/concurrent-chat-1.json
cp "$RUNNER_TEMP/concurrent-chat-2.json" .runtime/concurrent-chat-2.json
cp "$RUNNER_TEMP/policy-block.json" .runtime/policy-block.json

stream_payload=$(jq -nc \
  --arg chat_id "production-stream-${ACCEPTANCE_RUN_ID}" \
  --arg request_id "production-stream-request-${ACCEPTANCE_RUN_ID}" \
  '{chat_id:$chat_id,request_id:$request_id,message:"Give a concise explanation of why authenticated service bindings are used between Foundation and the private control plane.",mode:"chat",strict_zero_cost_only:true,require_model_generation:true}')
stream_json_status=$(curl -sS --max-time 90 \
  -o "$RUNNER_TEMP/live-stream-json.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: production-stream-json-${ACCEPTANCE_RUN_ID}" \
  -d "${stream_payload}" \
  "${BASE_URL}/api/v1/chat")
echo "POST /api/v1/chat with stream payload -> HTTP ${stream_json_status}"
cat "$RUNNER_TEMP/live-stream-json.json" || true
test "$stream_json_status" = '200' || {
  echo "stream-payload JSON probe failed:"
  cat "$RUNNER_TEMP/live-stream-json.json" || true
  exit 1
}
expected_stream_response_id="chat-production-stream-request-${ACCEPTANCE_RUN_ID}"
jq -e --arg expected_response_id "$expected_stream_response_id" '.ok == true and .response.response_id == $expected_response_id' "$RUNNER_TEMP/live-stream-json.json" >/dev/null || {
  echo "stream-payload JSON response contract failed:"
  cat "$RUNNER_TEMP/live-stream-json.json" || true
  exit 1
}

stream_status=$(curl -sS --no-buffer --max-time 90 \
  -D "$RUNNER_TEMP/live-stream.headers" \
  -o "$RUNNER_TEMP/live-stream.txt" \
  -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: production-stream-${ACCEPTANCE_RUN_ID}" \
  -d "${stream_payload}" \
  "${BASE_URL}/api/v1/chat/stream")
echo "POST /api/v1/chat/stream -> HTTP ${stream_status}"
echo '--- live-stream.headers ---'
cat "$RUNNER_TEMP/live-stream.headers" || true
echo '--- live-stream.body ---'
cat "$RUNNER_TEMP/live-stream.txt" || true
echo '--- end live-stream diagnostics ---'
test "$stream_status" = '200'
grep -qi '^Content-Type: text/event-stream' "$RUNNER_TEMP/live-stream.headers"
grep -q '^event: start' "$RUNNER_TEMP/live-stream.txt"
grep -q '^event: done' "$RUNNER_TEMP/live-stream.txt"
grep -q '"result_state":' "$RUNNER_TEMP/live-stream.txt"
echo "Live SSE lifecycle acceptance: PASS"
live_research_payload=$(jq -nc \
  '{question:"Production runtime acceptance: verify the public research path can ingest a permitted source without inventing facts.",depth:"quick",require_citations:true,max_sources:1,max_evidence_items:4,strict_zero_cost_only:true,source_urls:["https://example.com/"]}')
live_research_status=$(curl -sS --max-time 90 \
  -o "$RUNNER_TEMP/live-research.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H 'Content-Type: application/json' \
  -H "Idempotency-Key: production-research-${ACCEPTANCE_RUN_ID}" \
  -d "${live_research_payload}" \
  "${BASE_URL}/api/v1/research")
echo "POST /api/v1/research -> HTTP ${live_research_status}"
echo '--- live-research.body ---'
cat "$RUNNER_TEMP/live-research.json" || true
echo '--- end live-research diagnostics ---'
test "$live_research_status" = '200'
jq -e '.ok == true and (.run_id | type == "string" and length > 0)' \
  "$RUNNER_TEMP/live-research.json" >/dev/null
live_research_run_id=$(jq -r '.run_id' "$RUNNER_TEMP/live-research.json")

live_research_read_status=$(curl -sS --max-time 30 \
  -o "$RUNNER_TEMP/live-research-read.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  "${BASE_URL}/api/v1/research/${live_research_run_id}")
echo "GET /api/v1/research/${live_research_run_id} -> HTTP ${live_research_read_status}"
test "$live_research_read_status" = '200'
jq -e --arg run_id "${live_research_run_id}" \
  '.ok == true and ((.run_id // .run.run_id) == $run_id)' \
  "$RUNNER_TEMP/live-research-read.json" >/dev/null
echo "Live research execution/readback acceptance: PASS (${live_research_run_id})"

# Run the broader authenticated infrastructure diagnostic only after both deployments succeed.
if [ -n "${AUTH_TOKEN:-}" ]; then
  diagnostic_status=$(curl -sS -o diagnostic.json -w '%{http_code}' \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{"operation":"infrastructure_verify_public_test"}' \
    "$BASE_URL/api/v1/chatbot/diagnostic")
  echo "POST /api/v1/chatbot/diagnostic -> HTTP ${diagnostic_status}"
  cat diagnostic.json
  test "$diagnostic_status" = '200'
  jq -e '.ok == true and .status == "ok"
  and any(.checks[]?; .name == "public_chatbot" and .ok == true and .runtime_status == "ok")
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "d1_memory_store" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "d1_memory_query" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "memory_owner_boundary" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "task_envelope_d1_replay_guard" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "d1_candidate_learning_round_trip" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "durable_resource_reserve_consume" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "d1_reservation_reject_changes_semantics" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "d1_concurrent_overlimit_changes_semantics" and .ok == true)
  and any(((.checks // [])[] | (.runtime_checks // [])[]); .name == "maintenance_scheduler_reconciliation" and .ok == true)
  and any(.checks[]?; .name == "cloudflare_d1" and .ok == true)
  and any(.checks[]?; .name == "backblaze_b2_lifecycle" and .ok == true)
' diagnostic.json >/dev/null
else
  echo 'AUTH_TOKEN GitHub secret not configured; authenticated infrastructure diagnostic skipped.'
fi


# Remove reciprocal Service Bindings from the legacy pair before deletion. Cloudflare refuses
# deleting either side while the other Worker still references it. Keep every non-service binding
# intact so this migration step only severs the obsolete cross-worker edges.
for legacy_worker in "$legacy_private_worker" "$legacy_public_worker"; do
  if [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then
    legacy_settings_file="$RUNNER_TEMP/${legacy_worker}-settings.json"
    legacy_patch_file="$RUNNER_TEMP/${legacy_worker}-bindings.json"
    legacy_boundary="----cf-legacy-${RANDOM}-${RANDOM}"
    settings_status=$(curl -sS -o "$legacy_settings_file" -w '%{http_code}'       -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"       "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/$legacy_worker/settings" || true)
    if [ "$settings_status" = '404' ]; then
      echo "Legacy Worker $legacy_worker already absent; binding detach skipped"
      continue
    fi
    test "$settings_status" = '200'
    jq -e '.success == true and (.result.bindings | type == "array")' "$legacy_settings_file" >/dev/null
    jq -c '.result.bindings | map(select(.type != "service"))' "$legacy_settings_file" > "$legacy_patch_file"
    legacy_settings_json=$(jq -cn --slurpfile bindings "$legacy_patch_file" '{bindings: $bindings[0]}')
    legacy_multipart=$(printf -- '--%s\r\nContent-Disposition: form-data; name="settings"\r\nContent-Type: application/json\r\n\r\n%s\r\n--%s--\r\n'       "$legacy_boundary" "$legacy_settings_json" "$legacy_boundary")
    detach_status=$(curl -sS -o "$RUNNER_TEMP/${legacy_worker}-detach.json" -w '%{http_code}'       -X PATCH       -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}"       -H "Content-Type: multipart/form-data; boundary=${legacy_boundary}"       --data-binary "$legacy_multipart"       "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/$legacy_worker/settings" || true)
    echo "PATCH legacy Worker $legacy_worker service bindings -> HTTP $detach_status"
    if [ "$detach_status" != "200" ]; then
      jq -c '{success,message,errors}' "$RUNNER_TEMP/${legacy_worker}-detach.json" 2>/dev/null || true
      exit 1
    fi
    jq -e '.success == true and ((.result.bindings // []) | all(.type != "service"))' "$RUNNER_TEMP/${legacy_worker}-detach.json" >/dev/null
  fi
done

# Retire the legacy Worker pair only after the renamed pair has passed all live acceptance checks.
for legacy_worker in "$legacy_private_worker" "$legacy_public_worker"; do
  if [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then
    delete_status=$(curl -sS -o "$RUNNER_TEMP/legacy-worker-delete.json" -w '%{http_code}' \
      -X DELETE -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' \
      "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/$legacy_worker?force=true" || true)
    echo "DELETE legacy Worker $legacy_worker -> HTTP $delete_status"
    if [ "$delete_status" != "200" ] && [ "$delete_status" != "404" ]; then
      jq -c '{success,message,errors}' "$RUNNER_TEMP/legacy-worker-delete.json" 2>/dev/null || true
      exit 1
    fi
  fi
done
echo "Production release completed for ${GITHUB_SHA} using Operations ${OPERATIONS_REF}"