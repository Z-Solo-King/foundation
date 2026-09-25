const fs = require("fs");
const cp = require("child_process");
const path = require("path");

const root = path.resolve(__dirname, "..");
const workflow = fs.readFileSync(path.join(root, ".github/workflows/family-integrity-gate.yml"), "utf8");
const checker = fs.readFileSync(path.join(root, "scripts/family_integrity_check.js"), "utf8");

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(workflow.includes('cron: "45 17 * * *"'), "family integrity schedule missing");
assert(workflow.includes("node scripts/family_integrity_check.js"), "family integrity checker missing");
assert(workflow.includes("actions/upload-artifact@"), "integrity receipt upload missing");
assert(checker.includes("issues?state=open"), "live issue query missing");
assert(checker.includes("FAMILY_INTEGRITY_PASS"), "pass receipt missing");
assert(checker.includes("Foundation #282"), "stale-issue guard missing");
assert(checker.includes("Foundation #154"), "closed-credential stale guard missing");

cp.execFileSync("node", ["--check", path.join(root, "scripts/family_integrity_check.js")], {stdio:"inherit"});
console.log("family integrity static contract: PASS");
