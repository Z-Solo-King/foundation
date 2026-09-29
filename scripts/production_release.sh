#!/usr/bin/env bash
set -euo pipefail

OPERATIONS_REPOSITORY="Z-Solo-King/operations"
PIN_MANIFEST="docs/OPERATIONS_PIN_MANIFEST.json"
OPERATIONS_REF="$(python - "$PIN_MANIFEST" <<'PY'
import json, re, sys
manifest = json.load(open(sys.argv[1], encoding="utf-8"))
value = manifest["pins"]["production_runtime"]["sha"]
if not re.fullmatch(r"[0-9a-f]{40}", value):
    raise SystemExit("production Operations pin is not a 40-hex SHA")
print(value)
PY
)"
OPERATIONS_SERVICE_NAME="operations"
OPERATIONS_EDGE_SERVICE_NAME="operations-edge"
PUBLIC_WORKER_NAME="heroic"
PYTHON_CORE_WORKER_NAME="heroic-core"
BASE_URL="https://ai-cio.pages.dev"
ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${GITHUB_RUN_ATTEMPT:-1}"

cleanup() {
  rm -rf "$RUNNER_TEMP/operations" "$RUNNER_TEMP/operations-secrets.env" "$RUNNER_TEMP/public-secrets.env" \
    "$RUNNER_TEMP/git-askpass-operations.sh" "$RUNNER_TEMP/operations-app.pem" \
    "$RUNNER_TEMP/github-app-jwt.txt" "$RUNNER_TEMP/github-app-installation.json" \
    "$RUNNER_TEMP/github-app-installation-meta.json" wrangler.production.generated.toml wrangler.python-core.generated.toml health.json readiness.json frontend.html \
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

after_install_marker=''

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio coverage workers-py workers-runtime-sdk uv PyYAML jsonschema
uv --version
python -m compileall -q backend foundation_core worker.py
python -c "import foundation_core; print(foundation_core.__all__)"
coverage run --branch --source=backend,foundation_core,worker --omit='tests/*' -m pytest tests/ -v
coverage report --show-missing --fail-under=100 --omit='tests/*'
python -m benchmark.chatbot_query_benchmark --input benchmark/chatbot-query-corpus.json --output .runtime/chatbot-query-benchmark.json
python -m pytest -q tests/test_workflow_policy.py
node tests/public_edge_js_test.mjs
python scripts/public_security_lint.py --strict

test ! -e backend/learning/promotion.py
# The public Worker intentionally references the abstract OPERATIONS service binding.
# Scan production source for private implementation markers and concrete private
# service topology instead of the generic binding identifier.
! grep -RniE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' foundation_core backend wrangler.toml migrations
! grep -nE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' worker.py edge.js
! grep -RniE 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY|github_pat_[A-Za-z0-9_]+' foundation_core backend worker.py wrangler.toml migrations tests

token_verify_status=$(curl -sS -o "$RUNNER_TEMP/cloudflare-token-verify.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' \
  https://api.cloudflare.com/client/v4/user/tokens/verify || true)
if [ "$token_verify_status" != '200' ] || ! jq -e '.success == true and .result.status == "active"' "$RUNNER_TEMP/cloudflare-token-verify.json" >/dev/null 2>&1; then
  echo "Cloudflare token self-verify endpoint was not usable (HTTP $token_verify_status); continuing with account-scoped authorization check."
  jq -c '{success,message,result:{status:(.result.status // null),id:(.result.id // null)}}' "$RUNNER_TEMP/cloudflare-token-verify.json" 2>/dev/null || true
fi


# Preflight and stage the private Operations handoff before touching production.
key_file="$RUNNER_TEMP/operations-app.pem"
umask 077
printf '%s\n' \
  'name = "heroic-core"' \
  'main = "worker.py"' \
  'compatibility_date = "2026-09-09"' \
  'compatibility_flags = ["python_workers", "enable_request_signal", "request_signal_passthrough"]' \
  'workers_dev = false' \
  'preview_urls = false' \
  '' \
  '[assets]' \
  'directory = "./frontend"' \
  'binding = "ASSETS"' \
  'not_found_handling = "single-page-application"' \
  '' \
  '[[d1_databases]]' \
  'binding = "DB"' \
  "database_name = \"${database_name}\"" \
  "database_id = \"${database_id}\"" \
  '' \
  '[[services]]' \
  'binding = "OPERATIONS"' \
  "service = \"${OPERATIONS_EDGE_SERVICE_NAME}\"" \
  '' \
  '[secrets]' \
  'required = ["AUTH_TOKEN", "B2_KEY_ID", "B2_APPLICATION_KEY"]' \
  '' \
  '[vars]' \
  'ENVIRONMENT = "production"' \
  'STRICT_ZERO_COST_ONLY = "true"' \
  "RELEASE_FOUNDATION_SHA = \"${GITHUB_SHA}\"" \
  "RELEASE_OPERATIONS_REF = \"${OPERATIONS_REF}\"" \
  "B2_BUCKET = \"${B2_BUCKET}\"" \
  "B2_ENDPOINT = \"${B2_ENDPOINT}\""
  > wrangler.python-core.generated.toml

grep -q '^name = "heroic-core"$' wrangler.python-core.generated.toml
grep -q '^main = "worker.py"$' wrangler.python-core.generated.toml
grep -q '^directory = "./frontend"$' wrangler.python-core.generated.toml
grep -q '^binding = "ASSETS"$' wrangler.python-core.generated.toml
grep -q "^service = \"${OPERATIONS_EDGE_SERVICE_NAME}\"$" wrangler.python-core.generated.toml

printf '%s\n' \
  'name = "heroic"' \
  'main = "edge.js"' \
  'compatibility_date = "2026-09-28"' \
  'workers_dev = false' \
  'preview_urls = false' \
  '' \
  '[[services]]' \
  'binding = "CORE"' \
  "service = \"${PYTHON_CORE_WORKER_NAME}\""
  > wrangler.production.generated.toml

grep -q '^name = "heroic"$' wrangler.production.generated.toml
grep -q '^main = "edge.js"$' wrangler.production.generated.toml
grep -q '^binding = "CORE"$' wrangler.production.generated.toml
grep -q "^service = \"${PYTHON_CORE_WORKER_NAME}\"$" wrangler.production.generated.toml
! grep -q 'python_workers' wrangler.production.generated.toml
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
if [ -n "$legacy_public_worker" ] && [ -n "$legacy_private_worker" ]; then
  echo "Legacy Worker retirement inputs: configured"
else
  echo "Legacy Worker retirement: deferred (private migration inputs not configured)"
fi
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

# Deploy the migrated JavaScript edge Worker before Foundation so the public OPERATIONS binding
# targets the new edge transport boundary. The edge Worker calls the Python core privately.
(cd "$RUNNER_TEMP/operations/polyglot/edge-worker" && npx --yes wrangler@4.131.1 deploy --config wrangler.toml --message "github:${OPERATIONS_REF}" --tag "github:${OPERATIONS_REF}:edge-${ACCEPTANCE_RUN_ID}")
edge_deployments_status=$(curl -sS -o "$RUNNER_TEMP/edge-worker-deployments.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${OPERATIONS_EDGE_SERVICE_NAME}/deployments" || true)
echo "GET Operations edge deployments -> HTTP ${edge_deployments_status}"
test "$edge_deployments_status" = "200" || { cat "$RUNNER_TEMP/edge-worker-deployments.json"; exit 1; }
edge_version_id=$(jq -r '.result.deployments[0].versions[]? | select(.percentage == 100) | .version_id' "$RUNNER_TEMP/edge-worker-deployments.json" | head -n1)
test -n "$edge_version_id" || { echo 'No 100% active Operations edge Worker version found'; exit 1; }
echo "Operations edge Worker deployment: PASS (${OPERATIONS_EDGE_SERVICE_NAME})"




npx --yes wrangler@4.131.1 d1 migrations apply "$database_name" --remote --config wrangler.python-core.generated.toml
pywrangler deploy --config wrangler.python-core.generated.toml --secrets-file "$public_secret_file" --message "github:${GITHUB_SHA}:python-core"
(cd "$GITHUB_WORKSPACE" && npx --yes wrangler@4.131.1 deploy --config wrangler.production.generated.toml --message "github:${GITHUB_SHA}:javascript-edge")

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
npx --yes wrangler@4.131.1 d1 execute "$database_name" --remote \
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

# Verify the live protected policy bindings match repository authority after deployment.
operations_settings_status=$(curl -sS -o "$RUNNER_TEMP/operations-settings.json" -w '%{http_code}' \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/$OPERATIONS_SERVICE_NAME/settings" || true)
test "$operations_settings_status" = "200" || { echo "Operations settings verification failed: HTTP $operations_settings_status"; cat "$RUNNER_TEMP/operations-settings.json"; exit 1; }
jq -e '.success == true and any(.result.bindings[]?; .name == "CHAT_MODERATION_MODE" and .text == "block") and any(.result.bindings[]?; .name == "STRICT_ZERO_COST_ONLY" and .text == "true") and any(.result.bindings[]?; .name == "ALLOW_PAID_FALLBACK" and .text == "false") and any(.result.bindings[]?; .name == "ALLOW_UNKNOWN_PRICING" and .text == "false") and any(.result.bindings[]?; .name == "MAX_DAILY_COST_USD" and .text == "0")' "$RUNNER_TEMP/operations-settings.json" >/dev/null
echo "Operations protected policy bindings: PASS"

edge_active_status=$(curl -sS -o "$RUNNER_TEMP/edge-worker-active.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/workers/scripts/${OPERATIONS_EDGE_SERVICE_NAME}/deployments" || true)
echo "GET active Operations edge Worker -> HTTP ${edge_active_status}"
test "$edge_active_status" = "200"
edge_active_version_id=$(jq -r '.result.deployments[0].versions[]? | select(.percentage == 100) | .version_id' "$RUNNER_TEMP/edge-worker-active.json" | head -n1)
test -n "$edge_active_version_id"
echo "Operations edge Worker active deployment verification: PASS"

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
echo "Live memory/replay deployment-boundary acceptance: PASS"

# Record the live durable MODEL_CALLS quota state before the required model-generation
# acceptance. This is a bounded non-secret diagnostic: no auth token or provider payload
# is queried, only governance counters from the canonical D1 authority.
npx --yes wrangler@4.131.1 d1 execute "$database_name" --remote \
  --config="$RUNNER_TEMP/operations/wrangler.toml" \
  --command="SELECT scope, window_id, resource_kind, limit_units, reserved_units, consumed_units, updated_at FROM resource_governance_quota WHERE resource_kind = 'model_calls' ORDER BY updated_at DESC LIMIT 5;" \
  --json > "$RUNNER_TEMP/model-call-quota.json"
echo "model-call quota snapshot: collected"
cp "$RUNNER_TEMP/model-call-quota.json" .runtime/model-call-quota.json

npx --yes wrangler@4.131.1 d1 execute "$database_name" --remote \
  --config="$RUNNER_TEMP/operations/wrangler.toml" \
  --command="SELECT reservation_id, scope, window_id, resource_kind, amount, state, idempotency_key, lease_expires_at, updated_at FROM resource_governance_reservations WHERE resource_kind = 'model_calls' ORDER BY updated_at DESC LIMIT 10;" \
  --json > "$RUNNER_TEMP/model-call-reservations.json"
echo "model-call reservations snapshot: collected"
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
  if [ -n "$legacy_worker" ] && [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then
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
  if [ -n "$legacy_worker" ] && [ "$legacy_worker" != "foundation" ] && [ "$legacy_worker" != "operations" ]; then
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
echo "Production release completed for ${GITHUB_SHA}"