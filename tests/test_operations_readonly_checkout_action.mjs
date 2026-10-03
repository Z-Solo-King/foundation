import fs from "node:fs";
import path from "node:path";

const root = process.cwd();
const file = path.join(root, ".github/actions/operations-readonly-checkout/action.yml");
const text = fs.readFileSync(file, "utf8");

if (!text.includes("actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1")) throw new Error("missing pinned App token action");
if (!text.includes("permission-contents: read")) throw new Error("Operations action is not read-only");
if (!text.includes("persist-credentials: false")) throw new Error("checkout credentials are not discarded");
if (!text.includes("value: ${{ steps.operations-token.outputs.token }}")) throw new Error("token output is not exposed");
console.log("operations-readonly-checkout contract: PASS");
