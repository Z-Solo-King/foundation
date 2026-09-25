#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const root = path.join(process.cwd(), ".runtime", "nightly-ai-research");
const expectedJobs = 20;

function readJson(file, fallback = {}) {
  try { return JSON.parse(fs.readFileSync(file, "utf8")); }
  catch { return fallback; }
}

function excerpt(dir, names) {
  for (const name of names) {
    const file = path.join(dir, name);
    if (fs.existsSync(file)) return fs.readFileSync(file, "utf8").slice(0, 1800);
  }
  return "";
}

const dirs = fs.existsSync(root)
  ? fs.readdirSync(root, {withFileTypes: true})
      .filter(x => x.isDirectory() && x.name.startsWith("nightly-ai-research-"))
      .map(x => path.join(root, x.name))
      .filter(x => fs.existsSync(path.join(x, "metadata.json")))
      .sort()
  : [];

const jobs = dirs.map(dir => {
  const meta = readJson(path.join(dir, "metadata.json"));
  const github = readJson(path.join(dir, "github_summary.json"), {repositories:[]});
  return {
    job_id: meta.job_id,
    topic: meta.topic,
    target_issues: meta.target_issues || [],
    research_focus: meta.research_focus,
    lookback_since_utc: meta.lookback_since_utc,
    source_status: meta.source_status || {},
    github_repositories: (github.repositories || []).slice(0,5),
    reddit_excerpt: excerpt(dir, ["reddit.rss.excerpt","reddit_fallback.txt.excerpt","reddit.error.excerpt"]),
    x_twitter_excerpt: excerpt(dir, ["x_search.txt.excerpt","x.error.excerpt"]),
    evidence_class: "research-signal"
  };
});

const benchmarkTargets = [...new Set(jobs.flatMap(j => j.target_issues))].sort();
const sourceCounts = {};
for (const source of ["github_repositories","github_issues","reddit","x_twitter"]) {
  sourceCounts[source] = jobs.filter(j => j.source_status[source] === 200).length;
}

const candidates = {};
for (const job of jobs) {
  for (const issue of job.target_issues) {
    (candidates[issue] ||= []).push({
      job_id: job.job_id,
      topic: job.topic,
      focus: job.research_focus,
      next_action: "Turn the research signal into a deterministic benchmark/test/migration evidence task; independently reproduce before changing runtime or issue state.",
      evidence_class: "research-signal"
    });
  }
}

const report = {
  schema: "nightly-ai-research-report/v1",
  generated_at: new Date().toISOString(),
  expected_jobs: expectedJobs,
  jobs,
  benchmark_targets: benchmarkTargets,
  source_success_counts: sourceCounts
};

fs.mkdirSync(root, {recursive:true});
fs.writeFileSync(path.join(root, "nightly_ai_research_report.json"), JSON.stringify(report, null, 2) + "\n");
fs.writeFileSync(
  path.join(root, "benchmark_improvement_candidates.json"),
  JSON.stringify({
    schema:"nightly-ai-research-improvement-candidates/v1",
    generated_at:report.generated_at,
    evidence_class:"research-signal",
    by_issue:candidates
  }, null, 2) + "\n"
);

const lines = [
  "# Nightly AI research — 20-job synthesis",
  "",
  "Generated: " + report.generated_at,
  "Job packets: " + jobs.length + "/" + expectedJobs,
  "Benchmark targets: " + benchmarkTargets.join(", "),
  "",
  "## Source coverage",
  "",
  "- GitHub repositories: " + sourceCounts.github_repositories + "/" + expectedJobs,
  "- GitHub issues: " + sourceCounts.github_issues + "/" + expectedJobs,
  "- Reddit: " + sourceCounts.reddit + "/" + expectedJobs,
  "- X/Twitter: " + sourceCounts.x_twitter + "/" + expectedJobs,
  "",
  "## Research lanes",
  ""
];

for (const job of jobs) {
  lines.push("### " + job.job_id + " — " + job.topic);
  lines.push("Targets: " + job.target_issues.join(", "));
  lines.push("Focus: " + job.research_focus);
  lines.push(
    "Sources: GitHub repos=" + (job.source_status.github_repositories === 200 ? "PASS" : "MISS") +
    ", GitHub issues=" + (job.source_status.github_issues === 200 ? "PASS" : "MISS") +
    ", Reddit=" + (job.source_status.reddit === 200 ? "PASS" : "MISS") +
    ", X/Twitter=" + (job.source_status.x_twitter === 200 ? "PASS" : "MISS")
  );
  for (const repo of job.github_repositories) {
    lines.push("- " + repo.full_name + " — " + (repo.language || "unknown") + " — updated " + (repo.updated_at || "unknown") + " — " + repo.html_url);
  }
  if (job.reddit_excerpt.trim()) {
    lines.push("Reddit excerpt:");
    lines.push("~~~text");
    lines.push(job.reddit_excerpt.trim().slice(0, 900));
    lines.push("~~~");
  }
  if (job.x_twitter_excerpt.trim()) {
    lines.push("X/Twitter excerpt:");
    lines.push("~~~text");
    lines.push(job.x_twitter_excerpt.trim().slice(0, 900));
    lines.push("~~~");
  }
  lines.push("");
}

lines.push(
  "## Evidence boundary",
  "",
  "Research-signal evidence can propose benchmark fixtures, migration experiments, security tests, and evidence requests. It cannot certify runtime or production behavior.",
  "",
  "Promotion loop: research-signal → candidate benchmark slice → independent reproduction → regression fixture / issue update → nightly benchmark → runtime evidence where required."
);

fs.writeFileSync(path.join(root, "nightly_ai_research_report.md"), lines.join("\n") + "\n");

if (jobs.length !== expectedJobs) process.exitCode = 1;
