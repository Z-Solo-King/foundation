import test from "node:test";
import assert from "node:assert/strict";
import { CROSSFIRE_SURFACES, inspectCrossfireCoverage } from "../tools/crossfire_coverage_gate.mjs";

test("CrossFire coverage spans the major project surfaces", () => {
  const out = inspectCrossfireCoverage(process.cwd());
  for (const surface of Object.keys(CROSSFIRE_SURFACES)) {
    assert.equal(out.surfaces[surface].passed, true, JSON.stringify(out.surfaces[surface]));
  }
});

test("canonical CrossFire contracts are present", () => {
  const out = inspectCrossfireCoverage(process.cwd());
  for (const result of Object.values(out.contracts)) assert.equal(result.passed, true, JSON.stringify(result));
});

test("CrossFire scanner is deterministic and non-mutating", () => {
  const first = inspectCrossfireCoverage(process.cwd());
  const second = inspectCrossfireCoverage(process.cwd());
  assert.deepEqual(first, second);
  assert.equal(first.authority, "coverage_and_scheduling_only");
});

test("pinned action references are measurable rather than silently trusted", () => {
  const out = inspectCrossfireCoverage(process.cwd());
  assert.ok(out.action_reference_audit.total_uses >= out.action_reference_audit.pinned_refs);
  assert.ok(Array.isArray(out.action_reference_audit.unpinned_refs));
});
