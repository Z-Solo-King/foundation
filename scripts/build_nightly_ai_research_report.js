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
  ? fs.readdirSync(root, {withFileTypes:true})
      .filter(x => x.isDirectory() && x.name.startsWith("nightly-ai-research-"))
      .map(x => path.join(root, x.name))
      .filter(x => fs.existsSync(path.join(x, "metadata.json")))
      .sort()
  : [];

const jobs = dirs.map(dir => {
  const meta = readJson(path.join(dir, "metadata.json"));
  const github = readJson(path.join(dir, "github_summary.json"), {repositories:[]});
  const githubIssues = readJson(path.join(dir, "github_issue_summary.json"), {issues:[]});
  const githubSeeds = readJson(path.join(dir, "github_seed_summary.json"), {repositories:[]});
  return {
    job_id: meta.job_id,
    topic: meta.topic,
    target_issues: meta.target_issues || [],
    research_focus: meta.research_focus,
    family_graph_sha256: meta.family_graph_sha256 || "",
    lookback_since_utc: meta.lookback_since_utc,
    source_status: meta.source_status || {},
    github_repositories: (github.repositories || []).slice(0, 5),
    github_seed_repositories: (githubSeeds.repositories || []).slice(0, 5),
    seed_repository_count: githubSeeds.seed_count || 0,
    seed_repository_success_count: githubSeeds.seed_success || 0,
    github_issues: (githubIssues.issues || []).slice(0, 5),
    reddit_excerpt: excerpt(dir, ["reddit.rss.excerpt", "reddit_fallback.txt.excerpt", "reddit.error.excerpt"]),
    x_twitter_excerpt: excerpt(dir, ["x_search.txt.excerpt", "x.error.excerpt"]),
    evidence_class: "research-signal"
  };
});

const expectedIds = Array.from({length: expectedJobs}, (_, i) => String(i + 1).padStart(2, "0"));
const foundIds = new Set(jobs.map(j => j.job_id));
const missingJobs = expectedIds.filter(id => !foundIds.has(id));
const invalidJobs = jobs.filter(job => !Object.values(job.source_status).some(value => value === 200));
const familyGraphDigests = [...new Set(jobs.map(job => job.family_graph_sha256).filter(Boolean))];
const missingFamilyGraphJobs = jobs.filter(job => !job.family_graph_sha256).map(job => job.job_id);
const benchmarkTargets = [...new Set(jobs.flatMap(j => j.target_issues))].sort();
const acceptanceMatrixPath = path.join(process.cwd(), "docs", "OPEN_ISSUE_ACCEPTANCE_MATRIX.json");
const acceptanceMatrix = readJson(acceptanceMatrixPath, {issues:[]});
const openIssueIds = new Set(
  (acceptanceMatrix.issues || []).map(item => `${item.repo}#${item.number}`)
);
const staleBenchmarkTargets = benchmarkTargets.filter(issue => !openIssueIds.has(issue));

const sourceCounts = {};
for (const source of ["github_repositories", "github_issues", "github_seed_repositories", "reddit", "x_twitter"]) {
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

const CANDIDATE_RULES = [
  {matches:["parallel","orchestration","graph"], type:"orchestration", probe:"FI-01"},
  {matches:["token","context","memory","indexing"], type:"context_efficiency", probe:"FI-02"},
  {matches:["typed","decision","benchmark","evaluation"], type:"decision_evaluation", probe:"FI-03"},
  {matches:["research","evidence","search"], type:"evidence_provenance", probe:"FI-04"},
  {matches:["resource","inference","runtime"], type:"resource_inference", probe:"FI-05"},
  {matches:["security","supply","terminal"], type:"security_reliability", probe:"FI-06"},
  {matches:["observability","ci","actions"], type:"observability_ci", probe:"FI-07"},
  {matches:["recovery","browser","agent"], type:"recovery_agent", probe:"FI-08"},
  {matches:["migration","rust","go","typescript","java","kotlin","net","c++","zig"], type:"migration_portability", probe:"FI-09"}
];

function classifyCandidate(job) {
  const haystack = (job.topic + " " + job.research_focus).toLowerCase();
  const rule = CANDIDATE_RULES.find(item => item.matches.some(token => haystack.includes(token)));
  return rule || {type:"general_agent", probe:"FI-11"};
}

function buildSignalCandidates(jobList) {
  const rows = [];
  for (const job of jobList) {
    const classification = classifyCandidate(job);
    const supportingSources = [
      ...(job.github_seed_repositories || []).map(repo => ({
        source_type:"github_seed",
        title:repo.full_name,
        url:repo.html_url
      })),
      ...(job.github_repositories || []).map(repo => ({
        source_type:"github_repository",
        title:repo.full_name,
        url:repo.html_url
      })),
      ...(job.github_issues || []).map(issue => ({
        source_type: issue.pull_request ? "github_pull_request" : "github_issue",
        title: issue.title,
        url: issue.html_url
      }))
    ].slice(0, 8);

    for (const issue of job.target_issues) {
      rows.push({
        candidate_id: job.job_id + "-" + issue,
        issue,
        job_id: job.job_id,
        topic: job.topic,
        candidate_type: classification.type,
        benchmark_probe: classification.probe,
        focus: job.research_focus,
        source_status: job.source_status,
        supporting_sources: supportingSources,
        social_signal_present: Boolean(
          job.source_status.reddit === 200 || job.source_status.x_twitter === 200
        ),
        derivation:
          "Deterministic routing from the configured research topic/focus and collected source URLs; no model judgment is used to create the candidate.",
        next_test:
          "Create one bounded deterministic fixture for this candidate, reproduce independently, then decide whether it belongs in the benchmark, regression suite, migration review, or runtime evidence lane.",
        evidence_class:"research-signal"
      });
    }
  }
  return rows;
}

const signalCandidates = buildSignalCandidates(jobs);
const candidateTypes = [...new Set(signalCandidates.map(item => item.candidate_type))].sort();

const report = {
  schema: "nightly-ai-research-report/v2",
  generated_at: new Date().toISOString(),
  expected_jobs: expectedJobs,
  jobs,
  missing_jobs: missingJobs,
  invalid_jobs: invalidJobs.map(j => j.job_id),
  benchmark_targets: benchmarkTargets,
  open_issue_targets: [...openIssueIds].sort(),
  stale_benchmark_targets: staleBenchmarkTargets,
  source_success_counts: sourceCounts,
  family_graph_digests: familyGraphDigests,
  family_graph_digest_count: familyGraphDigests.length,
  missing_family_graph_jobs: missingFamilyGraphJobs,
  candidate_count: signalCandidates.length,
  candidate_types: candidateTypes,
  signal_candidates: signalCandidates
};

fs.mkdirSync(root, {recursive:true});
fs.writeFileSync(path.join(root, "nightly_ai_research_report.json"), JSON.stringify(report, null, 2) + "\n");
fs.writeFileSync(
  path.join(root, "benchmark_improvement_candidates.json"),
  JSON.stringify({
    schema: "nightly-ai-research-improvement-candidates/v2",
    generated_at: report.generated_at,
    evidence_class: "research-signal",
    by_issue: candidates,
    signal_candidates: signalCandidates,
    candidate_count: signalCandidates.length,
    candidate_types: candidateTypes
  }, null, 2) + "\n"
);

const lines = [
  "# Nightly AI research — 20-job synthesis",
  "",
  "Generated: " + report.generated_at,
  "Job packets: " + jobs.length + "/" + expectedJobs,
  "Missing packets: " + (missingJobs.length ? missingJobs.join(", ") : "none"),
  "Packets with zero live sources: " + (invalidJobs.length ? invalidJobs.map(j => j.job_id).join(", ") : "none"),
  "Family graph digest count: " + familyGraphDigests.length,
  "Jobs missing family graph digest: " + (missingFamilyGraphJobs.length ? missingFamilyGraphJobs.join(", ") : "none"),
  "Benchmark targets: " + benchmarkTargets.join(", "),
  "Stale benchmark targets: " + (staleBenchmarkTargets.length ? staleBenchmarkTargets.join(", ") : "none"),
  "Signal candidates: " + signalCandidates.length,
  "Candidate types: " + candidateTypes.join(", "),
  "",
  "## Source coverage",
  "",
  "- GitHub repository search: " + sourceCounts.github_repositories + "/" + expectedJobs,
  "- GitHub curated seed repositories: " + sourceCounts.github_seed_repositories + "/" + expectedJobs,
  "- GitHub issues/PRs: " + sourceCounts.github_issues + "/" + expectedJobs,
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
    ", GitHub issues/PRs=" + (job.source_status.github_issues === 200 ? "PASS" : "MISS") +
    ", GitHub seeds=" + (job.source_status.github_seed_repositories === 200 ? "PASS" : "MISS") +
    ", Reddit=" + (job.source_status.reddit === 200 ? "PASS" : "MISS") +
    ", X/Twitter=" + (job.source_status.x_twitter === 200 ? "PASS" : "MISS")
  );
  for (const repo of job.github_repositories) {
    lines.push("- Repo: " + repo.full_name + " — " + (repo.language || "unknown") + " — updated " + (repo.updated_at || "unknown") + " — " + repo.html_url);
  }
  for (const repo of job.github_seed_repositories) {
    lines.push("- Seed repo: " + repo.full_name + " — " + (repo.language || "unknown") + " — updated " + (repo.updated_at || "unknown") + " — " + repo.html_url);
  }
  for (const issue of job.github_issues) {
    lines.push("- GitHub: " + issue.title + " — " + (issue.pull_request ? "PR" : "issue") + " — updated " + (issue.updated_at || "unknown") + " — " + issue.html_url);
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
  "Research-signal evidence can propose benchmark fixtures, migration experiments, security tests, decision-fork cases, and evidence requests. Curated seed repositories are reference anchors, not endorsements or production authorities. It cannot certify runtime or production behavior.",
  "",
  "Promotion loop: research-signal → candidate benchmark slice → independent reproduction → regression fixture / issue update → nightly benchmark → runtime evidence where required.",
  "",
  "## Signal candidates",
  "",
  ...signalCandidates.slice(0, 60).map(candidate => "- " + candidate.candidate_id + " → " + candidate.issue + " → " + candidate.candidate_type + " → " + candidate.benchmark_probe + " — " + candidate.topic)

);

fs.writeFileSync(path.join(root, "nightly_ai_research_report.md"), lines.join("\n") + "\n");

if (
  jobs.length !== expectedJobs ||
  missingJobs.length ||
  invalidJobs.length ||
  familyGraphDigests.length !== 1 ||
  missingFamilyGraphJobs.length ||
  staleBenchmarkTargets.length ||
  signalCandidates.length === 0
) process.exitCode = 1;
