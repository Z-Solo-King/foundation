#!/usr/bin/env bash
set -euo pipefail

out=".runtime/nightly-ai-research/${JOB_ID}"
mkdir -p "$out"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
lookback="${LOOKBACK_HOURS:-24}"
since="$(date -u -d "${lookback} hours ago" +%Y-%m-%d 2>/dev/null || date -u -d "24 hours ago" +%Y-%m-%d)"
encode() { printf '%s' "$1" | jq -sRr @uri; }

gh_status=1
gh_issue_status=1
gh_seed_status=1
reddit_status=1
reddit_fallback_status=1
x_status=1

github_query="$(encode "${GITHUB_QUERY} updated:>=${since}")"
github_issue_query="$(encode "${GITHUB_QUERY} updated:>=${since}")"

if gh api -H 'Accept: application/vnd.github+json' "/search/repositories?q=${github_query}&sort=updated&order=desc&per_page=15" > "$out/github_repositories.json"; then
  gh_status=200
else
  printf '{"items":[]}\n' > "$out/github_repositories.json"
fi

if gh api -H 'Accept: application/vnd.github+json' "/search/issues?q=${github_issue_query}&sort=updated&order=desc&per_page=15" > "$out/github_issues.json"; then
  gh_issue_status=200
else
  printf '{"items":[]}\n' > "$out/github_issues.json"
fi

: > "$out/github_seed_repositories.json"
seed_count=0
seed_success=0
IFS=',' read -r -a seed_repos <<< "${SEED_REPOS:-}"
for repo in "${seed_repos[@]}"; do
  repo="$(printf '%s' "$repo" | xargs)"
  [ -n "$repo" ] || continue
  seed_count=$((seed_count + 1))
  if gh api -H 'Accept: application/vnd.github+json' "/repos/${repo}" | jq '{
      full_name, html_url, name, owner: .owner.login, description, language,
      stargazers_count, forks_count, open_issues_count, updated_at,
      archived, pushed_at, license: (.license.spdx_id // null)
    }' >> "$out/github_seed_repositories.json"; then
    seed_success=$((seed_success + 1))
  fi
done

if [ "$seed_success" -gt 0 ]; then
  gh_seed_status=200
else
  printf '%s\n' '{"error":"no seed repository metadata could be fetched"}' > "$out/github_seed_repositories.error"
fi

# Convert newline-delimited seed records into a valid array. Failed entries are omitted.
if [ "$seed_success" -gt 0 ]; then
  jq -s '.' "$out/github_seed_repositories.json" > "$out/github_seed_repositories.tmp"
  mv "$out/github_seed_repositories.tmp" "$out/github_seed_repositories.json"
else
  printf '[]\n' > "$out/github_seed_repositories.json"
fi

reddit_query="$(encode "${SOCIAL_QUERY}")"
if curl -fsSL --retry 2 --connect-timeout 5 --max-time 20 \
  -A 'Heroic-AI-nightly-research/1.2' \
  "https://www.reddit.com/search.rss?q=${reddit_query}&sort=new&t=day&limit=25" > "$out/reddit.rss"; then
  reddit_status=200
elif curl -fsSL --retry 2 --connect-timeout 5 --max-time 20 \
  "https://r.jina.ai/http://www.reddit.com/search/?q=${reddit_query}&sort=new&t=day" > "$out/reddit_fallback.txt"; then
  reddit_fallback_status=200
else
  printf '%s\n' 'Reddit unavailable in this run' > "$out/reddit.error"
fi

x_query="$(encode "${SOCIAL_QUERY} since:${since}")"
if curl -fsSL --retry 2 --connect-timeout 5 --max-time 25 \
  "https://r.jina.ai/http://x.com/search?q=${x_query}&f=live" > "$out/x_search.txt"; then
  x_status=200
else
  printf '%s\n' 'X/Twitter public search unavailable in this run' > "$out/x.error"
fi

jq '{
  count: (.items | length),
  repositories: [(.items // [])[] | {
    full_name, html_url, description, language,
    stargazers_count, forks_count, open_issues_count, updated_at
  }]
}' "$out/github_repositories.json" > "$out/github_summary.json"

jq '{
  count: (.items | length),
  issues: [(.items // [])[] | {
    repository_url, html_url, title, state, labels, updated_at,
    pull_request: (.pull_request // null)
  }]
}' "$out/github_issues.json" > "$out/github_issue_summary.json"

jq '{
  count: length,
  repositories: .,
  seed_count: '$seed_count',
  seed_success: '$seed_success'
}' "$out/github_seed_repositories.json" > "$out/github_seed_summary.json"

for f in reddit.rss reddit_fallback.txt reddit.error x_search.txt x.error; do
  if [ -f "$out/$f" ]; then head -c 12000 "$out/$f" > "$out/$f.excerpt"; fi
done

jq -n \
  --arg run_id "${GITHUB_RUN_ID}" \
  --arg attempt "${GITHUB_RUN_ATTEMPT}" \
  --arg job_id "${JOB_ID}" \
  --arg topic "${TOPIC}" \
  --arg started_at "${started_at}" \
  --arg since "${since}" \
  --argjson lookback "${lookback}" \
  --arg issues "${TARGET_ISSUES}" \
  --arg focus "${FOCUS}" \
  --arg seeds "${SEED_REPOS}" \
  --argjson gh_status "${gh_status}" \
  --argjson gh_issue_status "${gh_issue_status}" \
  --argjson gh_seed_status "${gh_seed_status}" \
  --argjson seed_count "${seed_count}" \
  --argjson seed_success "${seed_success}" \
  --argjson reddit_status "${reddit_status}" \
  --argjson reddit_fallback_status "${reddit_fallback_status}" \
  --argjson x_status "${x_status}" \
  '{
    schema:"nightly-ai-research-observation/v3",
    run_id:$run_id,
    run_attempt:$attempt,
    job_id:$job_id,
    topic:$topic,
    started_at:$started_at,
    lookback_hours:$lookback,
    lookback_since_utc:$since,
    target_issues:($issues|split(",")),
    research_focus:$focus,
    seed_repositories:($seeds|split(",")|map(select(length>0))),
    source_status:{
      github_repositories:$gh_status,
      github_issues:$gh_issue_status,
      github_seed_repositories:$gh_seed_status,
      reddit:$reddit_status,
      reddit_fallback:$reddit_fallback_status,
      x_twitter:$x_status
    },
    seed_repository_count:$seed_count,
    seed_repository_success_count:$seed_success,
    evidence_class:"research-signal",
    hidden_reasoning_recorded:false
  }' > "$out/metadata.json"

jq -e '.schema == "nightly-ai-research-observation/v3" and (.job_id|length>0) and (.topic|length>0) and (.target_issues|length>0) and (.research_focus|length>0) and (.seed_repositories|length>0) and (.evidence_class=="research-signal") and (.hidden_reasoning_recorded==false)' \
  "$out/metadata.json" >/dev/null

{
  echo "## ${TOPIC}"
  echo "- Job: ${JOB_ID}"
  echo "- Lookback: ${since} → ${started_at}"
  echo "- Target issues: ${TARGET_ISSUES}"
  echo "- Focus: ${FOCUS}"
  echo "- Seed repositories: ${SEED_REPOS}"
  echo "- GitHub repositories search: ${gh_status}"
  echo "- GitHub issues/PRs: ${gh_issue_status}"
  echo "- GitHub seed repositories: ${gh_seed_status} (${seed_success}/${seed_count})"
  echo "- Reddit: direct ${reddit_status}, fallback ${reddit_fallback_status}"
  echo "- X/Twitter: ${x_status}"
} >> "$GITHUB_STEP_SUMMARY"

if [ "$gh_status" -ne 200 ] && [ "$gh_issue_status" -ne 200 ] && [ "$gh_seed_status" -ne 200 ] && [ "$reddit_status" -ne 200 ] && [ "$reddit_fallback_status" -ne 200 ] && [ "$x_status" -ne 200 ]; then
  echo "All configured research sources unavailable; research packet recorded as failed." >&2
  exit 1
fi
