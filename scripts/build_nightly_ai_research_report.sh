#!/usr/bin/env bash
set -euo pipefail
root=".runtime/nightly-ai-research"
obj="$root/_objects"
mkdir -p "$obj"

for meta in "$root"/*/metadata.json; do
  [ -f "$meta" ] || continue
  dir="$(dirname "$meta")"
  id="$(jq -r '.job_id' "$meta")"
  repos="$dir/github_summary.json"
  [ -f "$repos" ] || printf '{"repositories":[]}
' > "$repos"
  jq --slurpfile gh "$repos" '{
    job_id:.job_id,
    topic:.topic,
    target_issues:.target_issues,
    research_focus:.research_focus,
    source_status:.source_status,
    github_repositories:(($gh[0].repositories // [])[:5]),
    evidence_class:"research-signal"
  }' "$meta" > "$obj/$id.json"
done

jobs_json="$(jq -s 'sort_by(.job_id)' "$obj"/*.json)"
missing_json="$(jq -n --argjson expected '["01","02","03","04","05","06","07","08","09","10","11","12","13","14","15","16","17","18","19","20"]' --argjson jobs "$jobs_json" '[ $expected[] | select(. as $id | ([ $jobs[].job_id ] | index($id) | not)) ]')"
targets_json="$(jq '[.[].target_issues[]] | unique | sort' <<<"$jobs_json")"

jq -n   --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)"   --argjson jobs "$jobs_json"   --argjson missing "$missing_json"   --argjson targets "$targets_json"   '{
    schema:"nightly-ai-research-report/v1",
    generated_at:$generated_at,
    expected_jobs:20,
    jobs:$jobs,
    missing_jobs:$missing,
    benchmark_targets:$targets
  }' > "$root/nightly_ai_research_report.json"

jq -n --arg generated_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" --argjson jobs "$jobs_json" '
  reduce $jobs[] as $job ({};
    reduce $job.target_issues[] as $issue (.; .[$issue] += [{
      job_id:$job.job_id,
      topic:$job.topic,
      focus:$job.research_focus,
      next_action:"Convert verified research signals into deterministic benchmark/test/migration evidence before changing runtime."
    }])
  )
  | {schema:"nightly-ai-research-improvement-candidates/v1",generated_at:$generated_at,evidence_class:"research-signal",by_issue:.}
' > "$root/benchmark_improvement_candidates.json"

{
  echo "# Nightly AI research — 20-job synthesis"
  echo
  echo "Generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Job packets: $(jq 'length' <<<"$jobs_json")/20"
  echo "Missing packets: $(jq -r 'if length==0 then "none" else join(", ") end' <<<"$missing_json")"
  echo
  echo "## Benchmark targets"
  jq -r '.[] | "- " + .' <<<"$targets_json"
} > "$root/nightly_ai_research_report.md"

[ "$(jq 'length' <<<"$jobs_json")" -eq 20 ]
[ "$(jq 'length' <<<"$missing_json")" -eq 0 ]
