#!/usr/bin/env bash
set -euo pipefail

OPERATIONS_REPOSITORY="Z-Solo-King/operations"
OPERATIONS_REF="d8825f5ce9c917a780c962f9773de6bb4446997f"
OPERATIONS_SERVICE_NAME="research-intelligence-engine-private"
BASE_URL="https://research-intelligence-engine-public.soloking-research-intelligence.workers.dev"

cleanup() {
  rm -rf "$RUNNER_TEMP/operations" "$RUNNER_TEMP/operations-secrets.env" \
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
test "$OPERATIONS_REF" = 'd8825f5ce9c917a780c962f9773de6bb4446997f'

after_install_marker=''

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio coverage workers-py workers-runtime-sdk uv
uv --version
python -m compileall -q backend foundation_core worker.py
python -c "import foundation_core; print(foundation_core.__all__)"
coverage run --branch --source=backend,foundation_core,worker --omit='tests/*,backend/persistence/artifacts.py' -m pytest tests/ -v
coverage report --show-missing --fail-under=100 --omit='tests/*,backend/persistence/artifacts.py'
python -m benchmark.chatbot_query_benchmark --input benchmark/chatbot-query-corpus.json --output .runtime/chatbot-query-benchmark.json
python -m pytest -q tests/test_workflow_policy.py
python scripts/public_security_lint.py --strict

test ! -e backend/learning/promotion.py
# The public Worker intentionally references the abstract OPERATIONS service binding.
# Scan production source for private implementation markers and concrete private
# service topology instead of the generic binding identifier.
! grep -RniE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE|research-intelligence-engine-private' foundation_core backend wrangler.toml migrations
! grep -nE 'extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE|research-intelligence-engine-private' worker.py
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

printf '%s\n' \
  'name = "research-intelligence-engine-public"' \
  'main = "worker.py"' \
  'compatibility_date = "2026-09-09"' \
  'compatibility_flags = ["python_workers"]' \
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
  'B2_BUCKET = "SoloKing"' \
  'B2_ENDPOINT = "https://s3.eu-central-003.backblazeb2.com"' \
  > wrangler.production.generated.toml

grep -q '^database_name = "research-intelligence"$' wrangler.production.generated.toml
grep -q '^directory = "./frontend"$' wrangler.production.generated.toml
grep -q '^binding = "ASSETS"$' wrangler.production.generated.toml
grep -q "^service = \"${OPERATIONS_SERVICE_NAME}\"$" wrangler.production.generated.toml
npx --yes wrangler@4.131.1 d1 migrations apply research-intelligence --remote --config wrangler.production.generated.toml
pywrangler deploy --config wrangler.production.generated.toml --message "github:${GITHUB_SHA}"

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

if [ -n "${AUTH_TOKEN:-}" ]; then
  diagnostic_status=$(curl -sS -o diagnostic.json -w '%{http_code}' \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{"operation":"infrastructure_verify_public_test"}' \
    "$BASE_URL/api/v1/chatbot/diagnostic")
  echo "POST /api/v1/chatbot/diagnostic -> HTTP ${diagnostic_status}"
  cat diagnostic.json
  test "$diagnostic_status" = '200'
  jq -e '.ok == true and .status == "ok" and .checks.public_chatbot == true and .checks.cloudflare_d1 == true and .checks.backblaze_b2_lifecycle == true' diagnostic.json >/dev/null
else
  echo 'AUTH_TOKEN GitHub secret not configured; authenticated infrastructure diagnostic skipped.'
fi

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
git -C "$RUNNER_TEMP/operations" fetch --no-tags --depth=1 origin "$OPERATIONS_REF"
git -C "$RUNNER_TEMP/operations" checkout --detach "$OPERATIONS_REF"
test "$(git -C "$RUNNER_TEMP/operations" rev-parse HEAD)" = "$OPERATIONS_REF"

npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote \
  --file="$RUNNER_TEMP/operations/docs/RESOURCE_GOVERNANCE_D1_SCHEMA.sql" \
  --config="$RUNNER_TEMP/operations/wrangler.toml"
secret_file="$RUNNER_TEMP/operations-secrets.env"
if [ -n "${AUTH_TOKEN:-}" ]; then
  printf 'AUTH_TOKEN=%s\n' "$AUTH_TOKEN" > "$secret_file"
  (cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:${OPERATIONS_REF}")
else
  echo 'AUTH_TOKEN is not configured in Foundation Actions; deploying Operations using already-configured protected remote secrets.'
  (cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --message "github:${OPERATIONS_REF}")
fi

echo "Production release completed for ${GITHUB_SHA} using Operations ${OPERATIONS_REF}"
