import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const executableRoots = [
  path.join(ROOT, ".github", "workflows"),
  path.join(ROOT, "scripts"),
  path.join(ROOT, "tools"),
];

const forbidden = [
  /gh\s+release\s+(create|upload|edit|rename)\b/i,
  /actions\/(create-release|upload-release-asset)\b/i,
  /softprops\/action-gh-release\b/i,
  /ncipollo\/release-action\b/i,
  /marvinpinto\/action-automatic-releases\b/i,
  /github\.com\/[^\s"']+\/releases\/download\//i,
  /github\.rest\.[A-Za-z0-9_$.]*release/i,
  /repos\/[\w.-]+\/[\w.-]+\/releases\b/i,
  /git\s+push[^\n]*(--tags|refs\/tags\/)/i,
];

const forbiddenFeedToken = /wc-google-feed-latest/i;

const feedWorkflows = new Set([
  ".github/workflows/commerce-feed-product-crawl.yml",
  ".github/workflows/woocommerce-google-xml-recovery-v19.yml",
  ".github/workflows/woocommerce-native-xml-recovery-v18.yml",
]);

function walk(dir) {
  if (!fs.existsSync(dir)) return [];
  const out = [];
  for (const ent of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, ent.name);
    if (ent.isDirectory()) out.push(...walk(p));
    else if (ent.isFile()) out.push(p);
  }
  return out;
}

const files = executableRoots
  .flatMap(walk)
  .filter((file) => /\.(ya?ml|mjs|js|sh|ts)$/.test(file));

const failures = [];

for (const file of files) {
  const rel = path.relative(ROOT, file).replaceAll(path.sep, "/");
  const body = fs.readFileSync(file, "utf8");

  for (const re of forbidden) {
    if (re.test(body)) {
      failures.push(`${rel}: forbidden release-publication primitive ${re}`);
    }
  }

  if (
    rel.startsWith(".github/workflows/") &&
    rel !== ".github/workflows/feed-release-governance.yml" &&
    forbiddenFeedToken.test(body)
  ) {
    failures.push(`${rel}: forbidden public feed release tag reference`);
  }

  if (
    feedWorkflows.has(rel) &&
    /(^|\n)\s*contents:\s*write\s*(\n|$)/i.test(body)
  ) {
    failures.push(`${rel}: feed workflow may not request contents: write`);
  }
}

if (failures.length) {
  console.error("Release publication policy FAILED");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`Release publication policy OK: scanned ${files.length} executable files.`);
