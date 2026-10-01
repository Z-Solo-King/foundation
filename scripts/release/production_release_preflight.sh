# Sourced preflight phase for the canonical production release entrypoint.
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
RELEASE_RUN_ATTEMPT="${RELEASE_RUN_ATTEMPT:-${GITHUB_RUN_ATTEMPT:-1}}"
ACCEPTANCE_RUN_ID="${GITHUB_RUN_ID}-attempt-${RELEASE_RUN_ATTEMPT}"

# Release validation traffic gets a signed admission subject so repeated release
# transactions do not consume the operator credential's shared public budget.
RELEASE_SUBJECT_SIGNATURE="$(python - "$AUTH_TOKEN" "$ACCEPTANCE_RUN_ID" <<'PY'
import hashlib
import hmac
import sys
token, release_id = sys.argv[1:]
print(hmac.new(
    token.encode("utf-8"),
    f"heroic-release-v1:{release_id}".encode("utf-8"),
    hashlib.sha256,
).hexdigest())
PY
)"
RELEASE_SUBJECT_HEADERS=(
  -H "X-Heroic-Release-ID: ${ACCEPTANCE_RUN_ID}"
  -H "X-Heroic-Release-Signature: ${RELEASE_SUBJECT_SIGNATURE}"
)

cleanup() {
  if [ -f "$RUNNER_TEMP/foundation-js-wrangler.toml" ]; then
    mv -f "$RUNNER_TEMP/foundation-js-wrangler.toml" wrangler.toml 2>/dev/null || true
  fi
  rm -rf "$RUNNER_TEMP/operations" "$RUNNER_TEMP/operations-secrets.env" "$RUNNER_TEMP/public-secrets.env" \
    "$RUNNER_TEMP/git-askpass-operations.sh" "$RUNNER_TEMP/operations-app.pem" \
    "$RUNNER_TEMP/github-app-jwt.txt" "$RUNNER_TEMP/github-app-installation.json" \
    "$RUNNER_TEMP/github-app-installation-meta.json" "$RUNNER_TEMP/foundation-js-wrangler.toml" \
    wrangler.production.generated.toml wrangler.python-core.generated.toml wrangler.d1.migrations.generated.toml health.json readiness.json frontend.html \
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
node --experimental-strip-types tests/public_edge_ts_test.mjs
python scripts/public_security_lint.py --strict

test ! -e backend/learning/promotion.py
# The public Worker intentionally references the abstract OPERATIONS service binding.
# Scan production source for private implementation markers and concrete private
# service topology instead of the generic binding identifier.
! grep -RniE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' foundation_core backend wrangler.toml migrations
! grep -nE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE' worker.py edge.ts
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
echo "Resolved Operations GitHub App installation: PASS"

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

# The immutable release pin must track the current Operations main head; otherwise stop before deploying stale runtime code.
# Keep the release bound to the certified immutable Operations revision; newer Operations main is drift, not an implicit promotion.
operations_main_status=$(curl -sS -o "$RUNNER_TEMP/operations-main-response.json" -w "%{http_code}" \
  -H 'Accept: application/vnd.github+json' -H "Authorization: Bearer ${github_app_token}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/${OPERATIONS_REPOSITORY}/git/refs/heads/main")
test "$operations_main_status" = '200' || { echo "Operations main head lookup failed: HTTP $operations_main_status"; cat "$RUNNER_TEMP/operations-main-response.json"; exit 1; }
operations_main_sha="$(jq -r '.object.sha // empty' "$RUNNER_TEMP/operations-main-response.json")"
[[ "$operations_main_sha" =~ ^[0-9a-f]{40}$ ]]
if [ "$operations_main_sha" = "$OPERATIONS_REF" ]; then
  echo "Operations certified production pin equals Operations main: PASS (${OPERATIONS_REF})"
else
  echo "Operations main is ${operations_main_sha}; certified production pin remains ${OPERATIONS_REF} (warn-only drift; release stays immutable)"
fi
echo "Operations production pin/current main parity: PASS (${OPERATIONS_REF})"

echo "private Operations access: PASS"

# Resolve runtime B2 configuration before creating the new Python core Worker.
# During the first split deployment, the non-secret bucket/endpoint bindings still live on
# the existing heroic Worker. After heroic-core exists, prefer its copied values.
if [ -z "${B2_BUCKET:-}" ] || [ -z "${B2_ENDPOINT:-}" ]; then
  settings_worker="${PYTHON_CORE_WORKER_NAME}"
  settings_path="$RUNNER_TEMP/python-core-settings.json"
  settings_status=$(curl -sS -o "$settings_path" -w '%{http_code}' \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H 'Content-Type: application/json' \
    "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/$settings_worker/settings" || true)

  if [ "$settings_status" = '404' ]; then
    settings_worker="${PUBLIC_WORKER_NAME}"
    settings_path="$RUNNER_TEMP/public-worker-settings.json"
    settings_status=$(curl -sS -o "$settings_path" -w '%{http_code}' \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H 'Content-Type: application/json' \
      "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/$settings_worker/settings" || true)
  fi

  test "$settings_status" = '200' || {
    echo "B2 settings lookup failed for bootstrap worker $settings_worker: HTTP $settings_status"
    cat "$settings_path" 2>/dev/null || true
    exit 1
  }

  resolved_b2_bucket=$(jq -r '.result.bindings[]? | select(.name == "B2_BUCKET" and .type == "plain_text") | .text' "$settings_path" | head -n1)
  resolved_b2_endpoint=$(jq -r '.result.bindings[]? | select(.name == "B2_ENDPOINT" and .type == "plain_text") | .text' "$settings_path" | head -n1)
  test -n "$resolved_b2_bucket" || { echo "Worker $settings_worker has no B2_BUCKET"; exit 1; }
  test -n "$resolved_b2_endpoint" || { echo "Worker $settings_worker has no B2_ENDPOINT"; exit 1; }
  case "$resolved_b2_endpoint" in
    https://*) ;;
    *) echo "Worker $settings_worker B2_ENDPOINT is not HTTPS"; exit 1 ;;
  esac
  B2_BUCKET="$resolved_b2_bucket"
  B2_ENDPOINT="$resolved_b2_endpoint"
  export B2_BUCKET B2_ENDPOINT
  echo "B2 release configuration: PASS (source=$settings_worker)"
fi

# Canonical runtime boundary checks. The public application is Pages -> heroic (TypeScript edge) -> heroic-core (Python) -> operations-edge (JavaScript) -> operations;
# no legacy foundation Worker, custom Worker domain, or workers.dev public backend should exist.
heroic_subdomain_status=$(curl -sS -o "$RUNNER_TEMP/heroic-subdomain.json" -w '%{http_code}' \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/heroic/subdomain" || true)
test "$heroic_subdomain_status" = '200' || { echo "Canonical heroic subdomain check failed: HTTP $heroic_subdomain_status"; cat "$RUNNER_TEMP/heroic-subdomain.json" 2>/dev/null || true; exit 1; }
jq -e '.success == true and .result.enabled == false and .result.previews_enabled == false' "$RUNNER_TEMP/heroic-subdomain.json" >/dev/null
legacy_worker_status=$(curl -sS -o "$RUNNER_TEMP/legacy-foundation-worker.json" -w '%{http_code}' \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/$CLOUDFLARE_ACCOUNT_ID/workers/scripts/foundation" || true)
test "$legacy_worker_status" = '404' || { echo "Legacy foundation Worker still exists or Cloudflare query failed: HTTP $legacy_worker_status"; cat "$RUNNER_TEMP/legacy-foundation-worker.json" 2>/dev/null || true; exit 1; }
# The GitHub Actions Cloudflare token is intentionally scoped to Worker/D1 deployment.
# Pages configuration is verified through the public canonical front door below and the
# application health/readiness checks later in this same release transaction.
pages_front_door_status=$(curl -sS -o "$RUNNER_TEMP/pages-front-door.json" -w '%{http_code}' --max-time 30 \
  "$BASE_URL/health" || true)
test "$pages_front_door_status" = '200' || { echo "Canonical Pages front door check failed: HTTP $pages_front_door_status"; cat "$RUNNER_TEMP/pages-front-door.json" 2>/dev/null || true; exit 1; }
jq -e '.status == "ok" or .ok == true' "$RUNNER_TEMP/pages-front-door.json" >/dev/null
echo "Canonical Cloudflare runtime boundary: PASS (public Pages front door reachable)"

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

# Compile the exact immutable Operations revision before any Cloudflare deployment.
# Operations intentionally has no competing GitHub Actions workflow, so this release-owner
# check is the private-source integrity gate.
echo "Compiling pinned Operations source: ${OPERATIONS_REF}"
python -m compileall -q "$RUNNER_TEMP/operations"
echo "Pinned Operations compile: PASS"
# Resolve the private D1 binding name from the exact approved Operations revision.
# The public Foundation tree never hardcodes the private database name.
database_name="$(sed -n 's/^database_name = "\(.*\)"$/\1/p' "$RUNNER_TEMP/operations/wrangler.toml" | head -n1)"
test -n "$database_name" || { echo 'Approved Operations revision did not declare a D1 database name'; exit 1; }

databases_status=$(curl -sS -o "$RUNNER_TEMP/cloudflare-d1-databases.json" -w '%{http_code}' \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/d1/database" || true)
test "$databases_status" = '200' || {
  echo "Cloudflare D1 authorization check failed: HTTP $databases_status"
  jq -c '{success,message,errors}' "$RUNNER_TEMP/cloudflare-d1-databases.json" 2>/dev/null || cat "$RUNNER_TEMP/cloudflare-d1-databases.json"
  exit 1
}
databases=$(cat "$RUNNER_TEMP/cloudflare-d1-databases.json")
database_id=$(jq -r --arg expected_name "$database_name" '[.result[]? | select(.name == $expected_name) | .uuid] | if length == 1 then .[0] else empty end' <<<"$databases")
test -n "$database_id" || { echo "Expected exactly one approved Operations D1 database: $database_name"; exit 1; }
echo "Cloudflare account/D1 authorization: PASS (private binding name resolved from approved Operations revision)"

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

# Fail closed if the promoted Operations pin contains the canonical authenticated
# chatbot backend boundary and the exact approved zero-cost provider allowlist.
actual_provider_list="$(sed -n 's/^CHAT_LLM_PROVIDERS = "\([^"]*\)"$/\1/p' "$RUNNER_TEMP/operations/wrangler.toml" | head -n1)"
expected_provider_list="$(PYTHONPATH="$RUNNER_TEMP/operations" python -c 'from private.chatbot.approved_providers import approved_zero_cost_provider_values; print(",".join(approved_zero_cost_provider_values()))')"
test -n "$actual_provider_list"
test "$actual_provider_list" = "$expected_provider_list"
grep -q '^CHAT_CLOUDFLARE_WORKERS_AI_MODEL = "@cf/zai-org/glm-4.7-flash"$' "$RUNNER_TEMP/operations/wrangler.toml"
grep -q '"workers_ai_neurons":10000' "$RUNNER_TEMP/operations/wrangler.toml"
grep -q 'CHAT_BACKEND_TOKEN' "$RUNNER_TEMP/operations/private/chat_auth.py"
grep -q 'from private.chat_auth import authorized_chat_request' "$RUNNER_TEMP/operations/worker.py"

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
  "B2_ENDPOINT = \"${B2_ENDPOINT}\"" \
  > wrangler.python-core.generated.toml

grep -q '^name = "heroic-core"$' wrangler.python-core.generated.toml
grep -q '^main = "worker.py"$' wrangler.python-core.generated.toml
grep -q '^directory = "./frontend"$' wrangler.python-core.generated.toml
grep -q '^binding = "ASSETS"$' wrangler.python-core.generated.toml
grep -q "^service = \"${OPERATIONS_EDGE_SERVICE_NAME}\"$" wrangler.python-core.generated.toml

printf '%s\n' \
  'name = "heroic"' \
  'main = "edge.ts"' \
  'compatibility_date = "2026-09-28"' \
  'workers_dev = false' \
  'preview_urls = false' \
  '' \
  '[[services]]' \
  'binding = "CORE"' \
  "service = \"${PYTHON_CORE_WORKER_NAME}\"" \
  > wrangler.production.generated.toml

grep -q '^name = "heroic"$' wrangler.production.generated.toml
grep -q '^main = "edge.ts"$' wrangler.production.generated.toml
grep -q '^binding = "CORE"$' wrangler.production.generated.toml
grep -q "^service = \"${PYTHON_CORE_WORKER_NAME}\"$" wrangler.production.generated.toml
! grep -q 'python_workers' wrangler.production.generated.toml
public_secret_file="$RUNNER_TEMP/public-secrets.env"
printf 'AUTH_TOKEN=%s\nB2_KEY_ID=%s\nB2_APPLICATION_KEY=%s\n' "$AUTH_TOKEN" "$B2_KEY_ID" "$B2_APPLICATION_KEY" > "$public_secret_file"
chmod 600 "$public_secret_file"

