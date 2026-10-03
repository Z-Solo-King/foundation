import test from "node:test";
import assert from "node:assert/strict";
import { validateOperationsGuard } from "../tools/validate_operations_main_guard.mjs";

const repo = {
  full_name: "Z-Solo-King/operations",
  private: true,
  default_branch: "main",
};
const approved = "11f592116d9ef57b6189bf8bf0ff0e95ec3d410f";
const newer = "37b35ba9e94600d746bc81e48cd2918b0c239bc7";
const cmp = (base, head, status) => ({
  status,
  base_commit: { sha: base },
  head_commit: { sha: head },
});

test("exact approved revision passes", () => {
  const r = validateOperationsGuard({
    repository: repo,
    mainBranch: { name: "main", commit: { sha: approved } },
    comparison: cmp(approved, approved, "identical"),
    workflowsPresent: false,
    approvedSha: approved,
  });
  assert.equal(r.status, "APPROVED_LINEAGE");
});

test("legitimate advancement of main passes when approved SHA is an ancestor", () => {
  const r = validateOperationsGuard({
    repository: repo,
    mainBranch: { name: "main", commit: { sha: newer } },
    comparison: cmp(approved, newer, "ahead"),
    workflowsPresent: false,
    approvedSha: approved,
  });
  assert.equal(r.status, "APPROVED_LINEAGE");
});

test("diverged lineage is rejected", () => {
  assert.throws(
    () =>
      validateOperationsGuard({
        repository: repo,
        mainBranch: { name: "main", commit: { sha: newer } },
        comparison: cmp(approved, newer, "diverged"),
        workflowsPresent: false,
        approvedSha: approved,
      }),
    /not an ancestor/,
  );
});

test("private workflow surface is rejected", () => {
  assert.throws(
    () =>
      validateOperationsGuard({
        repository: repo,
        mainBranch: { name: "main", commit: { sha: approved } },
        comparison: cmp(approved, approved, "identical"),
        workflowsPresent: true,
        approvedSha: approved,
      }),
    /.github\/workflows/,
  );
});

test("non-private repository is rejected", () => {
  assert.throws(
    () =>
      validateOperationsGuard({
        repository: { ...repo, private: false },
        mainBranch: { name: "main", commit: { sha: approved } },
        comparison: cmp(approved, approved, "identical"),
        workflowsPresent: false,
        approvedSha: approved,
      }),
    /remain private/,
  );
});

test("integrity workflow never publishes raw private inspection payloads", async () => {
  const fs = await import("node:fs/promises");
  const workflow = await fs.readFile(
    new URL("../.github/workflows/operations-private-freeplan-guard.yml", import.meta.url),
    "utf8",
  );
  assert.match(workflow, /\/raw\/repository\.json/);
  assert.match(workflow, /\/raw\/compare\.json/);
  assert.match(workflow, /failure\(\)/);
  assert.match(workflow, /private_metadata_omitted/);
  assert.doesNotMatch(workflow, /Observed main:/);
  assert.doesNotMatch(workflow, /Approved revision:/);
});
