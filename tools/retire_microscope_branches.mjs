#!/usr/bin/env node
/**
 * Deterministic branch-retirement executor for microscope consolidation.
 *
 * Policy:
 * - never delete the default/protected/active-PR/release-tag branch;
 * - exact same-tip groups are reduced to one keeper;
 * - branches whose tip is already contained in the default branch may be retired
 *   after live-reference checks and an age floor;
 * - unmerged/diverged branches are left untouched;
 * - all decisions are emitted as JSON evidence;
 * - execution is never forced and expected SHA is revalidated immediately before delete.
 */
import fs from "node:fs/promises";
import { execFileSync } from "node:child_process";

const execute = process.argv.includes("--execute");
const reportPath = process.argv.includes("--report")
  ? process.argv[process.argv.indexOf("--report") + 1]
  : "microscope-branch-retirement-report.json";
const minAgeHours = Math.max(0, Number(process.env.MICROSCOPE_MIN_AGE_HOURS ?? "24") || 24);
const repository = process.env.GITHUB_REPOSITORY;
if (!repository?.includes("/")) throw new Error("GITHUB_REPOSITORY is required");
const [owner, repo] = repository.split("/", 2);
let defaultBranch = "";
try {
  defaultBranch = exec("git", ["symbolic-ref", "--short", "refs/remotes/origin/HEAD"]).replace(
    /^origin\//,
    "",
  );
} catch {}
if (!defaultBranch) {
  defaultBranch = process.env.GITHUB_REF_NAME || "main";
}

function exec(command, args) {
  return execFileSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
  }).trim();
}
function ghPages(path, query = "") {
  const base = query ? `${path}?${query}&per_page=100` : `${path}?per_page=100`;
  const raw = exec("gh", ["api", "--paginate", "--slurp", base]);
  if (!raw) return [];
  const parsed = JSON.parse(raw);
  return Array.isArray(parsed) ? parsed.flat() : [];
}
function gitBranches() {
  const raw = exec("git", [
    "for-each-ref",
    "--format=%(refname:strip=3)\t%(objectname)",
    "refs/remotes/origin/",
  ]);
  return raw
    .split("\n")
    .filter(Boolean)
    .filter((line) => !line.startsWith("HEAD\t"))
    .map((line) => {
      const [name, sha] = line.split("\t");
      return { name, sha };
    });
}
function isAncestor(sha) {
  try {
    exec("git", ["merge-base", "--is-ancestor", sha, `origin/${defaultBranch}`]);
    return true;
  } catch {
    return false;
  }
}
function commitEpoch(sha) {
  return Number(exec("git", ["show", "-s", "--format=%ct", sha]));
}
function treeSha(sha) {
  return exec("git", ["rev-parse", sha + "^{tree}"]);
}
function referencedInLiveTree(branch) {
  try {
    const raw = exec("git", [
      "grep",
      "-l",
      "-F",
      "-e",
      branch,
      `origin/${defaultBranch}`,
      "--",
      ".github",
      "README.md",
      "docs",
      "scripts",
      "tools",
      "backend",
      "private",
      "foundation_core",
    ]);
    return raw
      .split("\n")
      .filter(Boolean)
      .filter(
        (path) =>
          !path.startsWith("docs/MICROSCOPE_") &&
          !path.startsWith("docs/HISTORY/") &&
          !path.startsWith("docs/private-archive/"),
      );
  } catch {
    return [];
  }
}
function referencedByReleaseOrTag(sha, name, tags, releases) {
  if (tags.some((tag) => tag?.commit?.sha === sha)) return "tag-target";
  if (releases.some((rel) => rel?.target_commitish === sha || rel?.target_commitish === name)) {
    return "release-target";
  }
  return null;
}

const protectedBranches = new Set(
  ghPages(`/repos/${owner}/${repo}/branches`, "protected=true").map((item) => item.name),
);
protectedBranches.add(defaultBranch);

const openPrs = ghPages(`/repos/${owner}/${repo}/pulls`, "state=open")
  .map((pr) => pr.head?.ref)
  .filter(Boolean);
const activePrHeads = new Set(openPrs);

const tags = ghPages(`/repos/${owner}/${repo}/tags`);
const releases = ghPages(`/repos/${owner}/${repo}/releases`);

const branches = gitBranches();
const groups = new Map();
for (const branch of branches) {
  if (!groups.has(branch.sha)) groups.set(branch.sha, []);
  groups.get(branch.sha).push(branch);
}
const now = Math.floor(Date.now() / 1000);
const defaultTreeSha = treeSha("origin/" + defaultBranch);
const decisions = [];

function keeperFor(group) {
  const priority =
    group.find((item) => item.name === defaultBranch) ??
    group.find((item) => activePrHeads.has(item.name)) ??
    group.find((item) => protectedBranches.has(item.name)) ??
    [...group].sort((a, b) => a.name.length - b.name.length || a.name.localeCompare(b.name))[0];
  return priority?.name ?? null;
}

for (const branch of branches) {
  const reasons = [];
  let disposition = "KEEP";
  let executable = false;

  if (branch.name === defaultBranch) reasons.push("default-branch");
  if (protectedBranches.has(branch.name)) reasons.push("protected");
  if (activePrHeads.has(branch.name)) reasons.push("active-pr-head");

  const releaseReason = referencedByReleaseOrTag(branch.sha, branch.name, tags, releases);
  if (releaseReason) reasons.push(releaseReason);

  const sameTip = groups.get(branch.sha) ?? [];
  const keeper = sameTip.length > 1 ? keeperFor(sameTip) : null;
  const treeIsCanonical = treeSha(branch.sha) === defaultTreeSha;

  const ageHours = (now - commitEpoch(branch.sha)) / 3600;

  if (!reasons.length && sameTip.length > 1 && branch.name !== keeper) {
    if (ageHours >= minAgeHours) {
      disposition = "RETIRE_EXACT_DUPLICATE";
      executable = true;
      reasons.push("same-tip-group", `age=${ageHours.toFixed(1)}h`);
    } else {
      reasons.push(`younger-than-${minAgeHours}h`);
    }
  } else if (
    !reasons.length &&
    (isAncestor(branch.sha) || treeIsCanonical) &&
    branch.sha !== exec("git", ["rev-parse", "origin/" + defaultBranch])
  ) {
    if (ageHours >= minAgeHours) {
      const refs = referencedInLiveTree(branch.name);
      if (refs.length) reasons.push(`live-reference:${refs.join(",")}`);
      else {
        disposition = treeIsCanonical ? "RETIRE_TREE_DUPLICATE" : "RETIRE_MERGED";
        executable = true;
        reasons.push(treeIsCanonical ? "tree-identical-to-default" : "tip-contained-in-default");
      }
    } else {
      reasons.push(`younger-than-${minAgeHours}h`);
    }
  }
  if (
    reasons.includes("active-pr-head") ||
    reasons.includes("protected") ||
    reasons.includes("default-branch") ||
    reasons.includes("tag-target") ||
    reasons.includes("release-target")
  ) {
    disposition = "KEEP";
    executable = false;
  }

  decisions.push({
    branch: branch.name,
    sha: branch.sha,
    disposition,
    executable,
    reasons,
    same_tip_group: sameTip.length > 1 ? sameTip.map((item) => item.name) : [],
    keeper,
  });
}

const execution = [];
for (const item of decisions.filter((row) => row.executable)) {
  const refPath = `/repos/${owner}/${repo}/git/refs/heads/${item.branch}`;
  try {
    const currentSha = exec("gh", ["api", refPath, "-q", ".object.sha"]);
    if (currentSha !== item.sha) {
      execution.push({
        branch: item.branch,
        action: "skipped",
        reason: "sha-changed",
        expected_sha: item.sha,
        current_sha: currentSha,
      });
      continue;
    }
    if (
      activePrHeads.has(item.branch) ||
      protectedBranches.has(item.branch) ||
      item.branch === defaultBranch
    ) {
      execution.push({ branch: item.branch, action: "skipped", reason: "safety-state-changed" });
      continue;
    }
    if (execute) {
      exec("gh", ["api", "--method", "DELETE", refPath]);
      execution.push({ branch: item.branch, action: "deleted", sha: item.sha });
    } else {
      execution.push({ branch: item.branch, action: "dry-run", sha: item.sha });
    }
  } catch (error) {
    execution.push({ branch: item.branch, action: "error", error: String(error) });
  }
}

const report = {
  schema: "microscope-branch-retirement/v1",
  repository,
  generated_at: new Date().toISOString(),
  default_branch: defaultBranch,
  branch_count: branches.length,
  exact_same_tip_groups: [...groups.values()].filter((group) => group.length > 1).length,
  tree_equivalent_to_default: decisions.filter((row) =>
    row.reasons.includes("tree-identical-to-default"),
  ).length,
  min_age_hours: minAgeHours,
  execute,
  decisions,
  execution,
};
await fs.writeFile(reportPath, JSON.stringify(report, null, 2) + "\n");
console.log(
  JSON.stringify(
    {
      schema: report.schema,
      repository,
      branches: branches.length,
      exact_duplicate_groups: report.exact_same_tip_groups,
      tree_equivalent_candidates: report.tree_equivalent_to_default,
      executable_candidates: decisions.filter((row) => row.executable).length,
      deleted: execution.filter((row) => row.action === "deleted").length,
      dry_run: execution.filter((row) => row.action === "dry-run").length,
      errors: execution.filter((row) => row.action === "error").length,
    },
    null,
    2,
  ),
);
