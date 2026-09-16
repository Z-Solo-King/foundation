#!/usr/bin/env bash
set -euo pipefail

OPERATIONS_REPOSITORY="Z-Solo-King/operations"
OPERATIONS_REF="cf28a28cb40de527aff1cd87f96e103669635f70"
BASE_URL="https://research-intelligence-engine-public.soloking-research-intelligence.workers.dev"

cleanup() {
  rm -rf \
    "$RUNNER_TEMP/operations" \
    "$RUNNER_TEMP/operations-secrets.env" \
    "$RUNNER_TEMP/git-askpass-operations.sh" \
    "$RUNNER_TEMP/operations-app.pem" \
    "$RUNNER_TEMP/github-app-jwt.txt" \
    "$RUNNER_TEMP/github-app-installation.json" \
    wrangler.production.generated.toml \
    readiness.json \
    frontend.html \
    /tmp/styles.css /tmp/app.js /tmp/composer.js /tmp/lifecycle_controller.js
}
trap cleanup EXIT

test -n "${CLOUDFLARE_API_TOKEN:-}" || { echo 'Missing CLOUDFLARE_API_TOKEN GitHub secret'; exit 1; }
test -n "${CLOUDFLARE_ACCOUNT_ID:-}" || { echo 'Missing CLOUDFLARE_ACCOUNT_ID GitHub secret. Add it in GitHub Actions settings; do not commit it.'; exit 1; }

test "${OPERATIONS_REF}" = 'cf28a28cb40de527aff1cd87f96e103669635f70'

python -m pip install --upgrade pip
python -m pip install -e .
python -m pip install pytest pytest-asyncio coverage workers-py workers-runtime-sdk

python -m compileall -q backend foundation_core worker.py
python -c "import foundation_core; print(foundation_core.__all__)"
coverage run --branch --source=backend,foundation_core,worker --omit='tests/*,backend/persistence/artifacts.py' -m pytest tests/ -v
coverage report --show-missing --fail-under=100 --omit='tests/*,backend/persistence/artifacts.py'
python -m benchmark.chatbot_query_benchmark --input benchmark/chatbot-query-corpus.json --output .runtime/chatbot-query-benchmark.json
python -m pytest -q tests/test_workflow_policy.py
python scripts/public_security_lint.py --strict

test ! -e backend/learning/promotion.py
! grep -RniE 'operations|extractor_mapper|private\.chatbot|resource_ledger|promotion\.py|trust_boundary|CONTROL_PLANE|research-intelligence-engine-private' foundation_core backend worker.py wrangler.toml migrations tests
test ! -e backend/learning/promotion.py
! grep -RniE 'BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY|AWS_SECRET_ACCESS_KEY|github_pat_[A-Za-z0-9_]+' foundation_core backend worker.py wrangler.toml migrations tests

curl -fsS \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  https://api.cloudflare.com/client/v4/user/tokens/verify \
  | jq -e '.success == true and .result.status == "active"' >/dev/null

databases=$(curl -fsS \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H 'Content-Type: application/json' \
  "https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/d1/database")
database_id=$(jq -r '[.result[]? | select(.name == "research-intelligence") | .uuid] | if length == 1 then .[0] else empty end' <<<"$databases")
test -n "$database_id" || { echo 'Expected exactly one research-intelligence D1 database'; exit 1; }

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
  'not_found_handling = "single-page-application"' \
  '' \
  '[[d1_databases]]' \
  'binding = "DB"' \
  'database_name = "research-intelligence"' \
  "database_id = \"${database_id}\"" \
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

npx --yes wrangler@4.131.1 d1 migrations apply research-intelligence --remote --config wrangler.production.generated.toml
pywrangler deploy --config wrangler.production.generated.toml --message "github:${GITHUB_SHA}"

health=$(curl -fsS "$BASE_URL/health")
jq -e '.ok == true' <<<"$health" >/dev/null
readiness=$(curl -fsS -o readiness.json -w '%{http_code}' "$BASE_URL/readiness")
test "$readiness" = '200'
jq -e '.ready == true and .database == true' readiness.json >/dev/null
ui=$(curl -fsS -o frontend.html -w '%{http_code}' "$BASE_URL/")
test "$ui" = '200'
grep -q '<title>Heroic AI — Chat & Research</title>' frontend.html
test -s frontend.html
for asset in styles.css app.js composer.js lifecycle_controller.js; do
  asset_status=$(curl -fsS -o "/tmp/${asset}" -w '%{http_code}' "$BASE_URL/${asset}")
  test "$asset_status" = '200'
  test -s "/tmp/${asset}"
done
if [ -n "${AUTH_TOKEN:-}" ]; then
  diagnostic=$(curl -fsS \
    -H "Authorization: Bearer ${AUTH_TOKEN}" \
    -H 'Content-Type: application/json' \
    -d '{"operation":"infrastructure_verify_public_test"}' \
    "$BASE_URL/api/v1/chatbot/diagnostic")
  jq -e '.ok == true and .status == "ok" and .checks.public_chatbot == true and .checks.cloudflare_d1 == true and .checks.backblaze_b2_lifecycle == true' <<<"$diagnostic" >/dev/null
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
proc = subprocess.run(
    ["openssl", "dgst", "-sha256", "-sign", key_file],
    input=unsigned,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    check=True,
)
print(unsigned.decode() + "." + b64url(proc.stdout))
PY

app_jwt=$(cat "$RUNNER_TEMP/github-app-jwt.txt")
installation_response=$(curl -fsS \
  -X POST \
  -H 'Accept: application/vnd.github+json' \
  -H "Authorization: Bearer ${app_jwt}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/app/installations/${OPERATIONS_APP_INSTALLATION_ID}/access_tokens")
printf '%s\n' "$installation_response" > "$RUNNER_TEMP/github-app-installation.json"
github_app_token=$(python - "$RUNNER_TEMP/github-app-installation.json" <<'PY'
import json
import sys
print(json.load(open(sys.argv[1], encoding='utf-8'))['token'])
PY
)
test -n "$github_app_token"
echo "::add-mask::$github_app_token"

repo_response=$(curl -fsS \
  -H 'Accept: application/vnd.github+json' \
  -H "Authorization: Bearer ${github_app_token}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/${OPERATIONS_REPOSITORY}")
jq -e --arg repo "$OPERATIONS_REPOSITORY" '.full_name == $repo and .private == true' <<<"$repo_response" >/dev/null
ref_response=$(curl -fsS \
  -H 'Accept: application/vnd.github+json' \
  -H "Authorization: Bearer ${github_app_token}" \
  -H 'X-GitHub-Api-Version: 2022-11-28' \
  "https://api.github.com/repos/${OPERATIONS_REPOSITORY}/git/commits/${OPERATIONS_REF}")
jq -e --arg expected "$OPERATIONS_REF" '.sha == $expected' <<<"$ref_response" >/dev/null

askpass="$RUNNER_TEMP/git-askpass-operations.sh"
umask 077
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

npx --yes wrangler@4.131.1 d1 execute research-intelligence --remote --file="$RUNNER_TEMP/operations/docs/RESOURCE_GOVERNANCE_D1_SCHEMA.sql" --config="$RUNNER_TEMP/operations/wrangler.toml"

secret_file="$RUNNER_TEMP/operations-secrets.env"
umask 077
if [ -n "${AUTH_TOKEN:-}" ]; then
  printf 'AUTH_TOKEN=%s\n' "$AUTH_TOKEN" > "$secret_file"
  (cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --secrets-file "$secret_file" --message "github:${OPERATIONS_REF}")
else
  echo 'AUTH_TOKEN is not configured in Foundation Actions; deploying Operations without protected authentication.'
  (cd "$RUNNER_TEMP/operations" && pywrangler deploy --config wrangler.toml --message "github:${OPERATIONS_REF}")
fi

echo "Production release completed for ${GITHUB_SHA}"