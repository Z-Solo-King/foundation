#!/usr/bin/env bash
set -euo pipefail

out=".runtime/nightly-ai-research/${JOB_ID}"
mkdir -p "$out"
started_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
lookback="${LOOKBACK_HOURS:-24}"
since="$(date -u -d "${lookback} hours ago" +%Y-%m-%d 2>/dev/null || date -u -d "24 hours ago" +%Y-%m-%d)"
encode() { printf '%s' "$1" | jq -sRr @uri; }

gh_status=1
reddit_status=1
reddit_fallback_status=1
x_status=1

github_query="$(encode "${GITHUB_QUERY} updated:>=${since}")"
if gh api -H 'Accept: application/vnd.github+json' "/search/repositories?q=${github_query}&sort=updated&order=desc&per_page=20" > "$out/github_repositories.json"; then
  gh_status=200
else
  printf '{"items":[]}
' > "$out/github_repositories.json"
fi

reddit_query="$(encode "${SOCIAL_QUERY}")"
if curl -fsSL --retry 2 --connect-timeout 5 --max-time 20 -A 'Heroic-AI-nightly-research/1.0'   "https://www.reddit.com/search.rss?q=${reddit_query}&sort=new&t=day&limit=25" > "$out/reddit.rss"; then
  reddit_status=200
elif curl -fsSL --retry 2 --connect-timeout 5 --max-time 20   "https://r.jina.ai/http://www.reddit.com/search/?q=${reddit_query}&sort=new&t=day" > "$out/reddit_fallback.txt"; then
  reddit_fallback_status=200
else
  printf '%s
' 'Reddit unavailable in this run' > "$out/reddit.error"
fi

x_query="$(encode "${SOCIAL_QUERY} since:${since}")"
if curl -fsSL --retry 2 --connect-timeout 5 --max-time 25   "https://r.jina.ai/http://x.com/search?q=${x_query}&f=live" > "$out/x_search.txt"; then
  x_status=200
else
  printf '%s
' 'X/Twitter public search unavailable in this run' > "$out/x.error"
fi

jq '{
  count: (.items | length),
  repositories: [(.items // [])[] | {
    full_name, html_url, description, language,
    stargazers_count, forks_count, open_issues_count, updated_at
  }]
}' "$out/github_repositories.json" > "$out/github_summary.json"

for f in reddit.rss reddit_fallback.txt reddit.error x_search.txt x.error; do
  if [ -f "$out/$f" ]; then head -c 12000 "$out/$f" > "$out/$f.excerpt"; fi
done

jq -n   --arg run_id "${GITHUB_RUN_ID}"   --arg attempt "${GITHUB_RUN_ATTEMPT}"   --arg job_id "${JOB_ID}"   --arg topic "${TOPIC}"   --arg started_at "${started_at}"   --arg since "${since}"   --argjson lookback "${lookback}"   --arg issues "${TARGET_ISSUES}"   --arg focus "${FOCUS}"   --argjson gh_status "${gh_status}"   --argjson reddit_status "${reddit_status}"   --argjson reddit_fallback_status "${reddit_fallback_status}"   --argjson x_status "${x_status}"   '{
    schema:"nightly-ai-research-observation/v1",
    run_id:$run_id,
    run_attempt:$attempt,
    job_id:$job_id,
    topic:$topic,
    started_at:$started_at,
    lookback_hours:$lookback,
    lookback_since_utc:$since,
    target_issues:($issues|split(",")),
    research_focus:$focus,
    source_status:{
      github_repositories:$gh_status,
      reddit:$reddit_status,
      reddit_fallback:$reddit_fallback_status,
      x_twitter:$x_status
    },
    evidence_class:"research-signal",
    hidden_reasoning_recorded:false
  }' > "$out/metadata.json"

jq -e '.schema == "nightly-ai-research-observation/v1" and (.job_id|length>0) and (.topic|length>0) and (.target_issues|length>0) and (.research_focus|length>0) and (.evidence_class=="research-signal") and (.hidden_reasoning_recorded==false)'   "$out/metadata.json" >/dev/null

{
  echo "## ${TOPIC}"
  echo "- Job: ${JOB_ID}"
  echo "- Lookback: ${since} → ${started_at}"
  echo "- Target issues: ${TARGET_ISSUES}"
  echo "- Focus: ${FOCUS}"
  echo "- GitHub repositories: ${gh_status}"
  echo "- Reddit: direct ${reddit_status}, fallback ${reddit_fallback_status}"
  echo "- X/Twitter: ${x_status}"
} >> "$GITHUB_STEP_SUMMARY"

if [ "$gh_status" -ne 200 ] && [ "$reddit_status" -ne 200 ] && [ "$reddit_fallback_status" -ne 200 ] && [ "$x_status" -ne 200 ]; then
  echo "All configured research sources unavailable; research packet recorded as failed." >&2
  exit 1
fi
