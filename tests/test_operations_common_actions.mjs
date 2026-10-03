import fs from "node:fs";
import path from "node:path";

const token = fs.readFileSync(path.join(process.cwd(), ".github/actions/operations-app-token/action.yml"), "utf8");
const checkout = fs.readFileSync(path.join(process.cwd(), ".github/actions/operations-readonly-checkout/action.yml"), "utf8");
for (const [label, text] of [["token", token], ["checkout", checkout]]) {
  if (!text.includes("actions/")) throw new Error(`${label} action is malformed`);
}
if (!token.includes("actions/create-github-app-token@bcd2ba49218906704ab6c1aa796996da409d3eb1")) throw new Error("App token pin missing");
if (!token.includes("permission-contents: read")) throw new Error("App token is not read-only");
if (!checkout.includes("actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1")) throw new Error("checkout pin missing");
if (!checkout.includes("persist-credentials: false")) throw new Error("checkout credentials are retained");
console.log("Operations common actions contract: PASS");
