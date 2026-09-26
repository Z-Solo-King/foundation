#!/usr/bin/env bash
set -euo pipefail
outdir=.runtime/security
mkdir -p "$outdir"
tree_file="$outdir/current-tree-matches.txt"
history_file="$outdir/history-matches.txt"
receipt="$outdir/full-secret-scan.json"
: >"$tree_file"
: >"$history_file"
patterns=(
  '-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----'
  'AKIA[0-9A-Z]{16}'
  'ASIA[0-9A-Z]{16}'
  'ghp_[A-Za-z0-9]{36}'
  'github_pat_[A-Za-z0-9_]{20,}'
  'xox[baprs]-[0-9A-Za-z-]{20,}'
)
for pattern in "${patterns[@]}"; do
  git grep --no-color -nI -E "$pattern" -- . >>"$tree_file" || true
  git log --all --no-ext-diff --unified=0 -G "$pattern" --pretty=format:%H -- >>"$history_file" || true
done
git grep --no-color -nI -E '(^|[[:space:]])Bearer[[:space:]]+[A-Za-z0-9._~+/-]{32,}' -- . >>"$tree_file" || true
git grep --no-color -nI -E 'api[_-]?key[[:space:]]*[:=][[:space:]]*["'"'"'][A-Za-z0-9._~+/-]{16,}' -- . >>"$tree_file" || true
sort -u "$tree_file" -o "$tree_file"
sort -u "$history_file" -o "$history_file"
tree_count=$(grep -c . "$tree_file" || true)
history_count=$(grep -c . "$history_file" || true)
status=PASS
if [[ "$tree_count" -ne 0 || "$history_count" -ne 0 ]]; then status=FAIL; fi
cat >"$receipt" <<EOF
{"schema":"public-full-secret-scan/v1","status":"$status","current_tree_matches":$tree_count,"history_matching_commits":$history_count,"history_depth":"$(git rev-list --count --all)","head":"$(git rev-parse HEAD)"}
EOF
cat "$receipt"
if [[ "$status" != PASS ]]; then
  cat "$tree_file" >&2 || true
  cat "$history_file" >&2 || true
  exit 1
fi
