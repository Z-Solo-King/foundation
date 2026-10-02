import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.cwd());

test("nightly dry-run gates live runtime verification after mode selection", () => {
  const text = fs.readFileSync(
    path.join(ROOT, ".github/workflows/nightly-multi-agent-research-v3.yml"),
    "utf8",
  );
  const modeStart = text.indexOf("      - name: Research mode");
  const probeStart = text.indexOf("      - name: Verify exact deployed research runtime");
  assert.ok(modeStart >= 0);
  assert.ok(probeStart > modeStart);
  assert.equal((text.match(/      - name: Research mode/g) ?? []).length, 1);

  const probeEnd = text.indexOf("      - name: Authenticate private research source", probeStart);
  const probeBlock = text.slice(probeStart, probeEnd);
  assert.match(probeBlock, /if: \$\{\{ inputs\.dry_run != true \}\}/);
  assert.match(probeBlock, /node scripts\\/nightly_runtime_contract_probe\\.mjs/);

  const crossfireStart = text.indexOf("      - name: Run complete crossfire research");
  const materializeStart = text.indexOf(
    "      - name: Materialize and validate lane artifacts",
    crossfireStart,
  );
  const crossfireBlock = text.slice(crossfireStart, materializeStart);
  assert.match(crossfireBlock, /args\\+=\\(--dry-run\\)/);
});
