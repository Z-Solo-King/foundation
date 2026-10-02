import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { validateChatResponse } from "../scripts/nightly_runtime_contract_probe.mjs";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("nightly v3 is dispatch-only and uses Node runtime probe/proxy", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-multi-agent-research-v3.yml"), "utf8");
  assert.equal(text.includes("schedule:"), false);
  assert.match(text, /workflow_dispatch:/);
  assert.match(text, /production_release_run_id/);
  assert.match(text, /operations_research_ref/);
  assert.match(text, /node scripts\/nightly_runtime_contract_probe\.mjs/);
  assert.match(text, /node scripts\/research_worker_proxy\.mjs/);
  assert.equal(text.includes('python -m pip install --disable-pip-version-check "httpx>=0.27,<1"'), false);
});

test("provider preflight delegates to the exact Node probe", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-research-provider-preflight.yml"), "utf8");
  assert.match(text, /workflow_dispatch:/);
  assert.match(text, /operations_research_ref/);
  assert.match(text, /node scripts\/nightly_runtime_contract_probe\.mjs/);
  assert.equal(text.includes("X-Heroic-Research-Proof"), false);
  assert.equal(text.includes("api/v1/chat"), false);
});

test("release still gates nightly on exact preflight", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/heroic-ai-production-release.yml"), "utf8");
  assert.match(text, /Preflight exact nightly runtime before research dispatch/);
  assert.match(text, /gh workflow run nightly-research-provider-preflight\.yml/);
  assert.match(text, /Research preflight failed; refusing to launch nightly\./);
  assert.match(text, /gh workflow run nightly-multi-agent-research-v3\.yml/);
});

test("Node probe validates authenticated nested research response", () => {
  const payload = {
    ok: true,
    request_id: "nightly-contract-probe-1",
    response: {
      response_id: "chat-nightly-contract-probe-1",
      provider: "cloudflare_workers_ai",
      generation_status: "model_generated",
      text: JSON.stringify({ findings: [], follow_up_questions: [], note: "probe" }),
    },
  };
  const [ok, details] = validateChatResponse(payload, "@cf/zai-org/glm-4.7-flash");
  assert.equal(ok, true);
  assert.equal(details.provider, "cloudflare_workers_ai");
  assert.equal(details.response_id_present, true);
  assert.equal(details.structured_output, true);
});

test("Node probe rejects deterministic fallback without provider proof", () => {
  const payload = {
    ok: true,
    response: {
      response_id: "chat-probe",
      generation_status: "deterministic_fallback",
      text: JSON.stringify({ findings: [], follow_up_questions: [], note: "probe" }),
    },
  };
  const [ok] = validateChatResponse(payload, "@cf/zai-org/glm-4.7-flash");
  assert.equal(ok, false);
});

test("Node probe output path contains no response-body or token dump", () => {
  const text = fs.readFileSync(path.join(ROOT, "scripts/nightly_runtime_contract_probe.mjs"), "utf8");
  assert.equal(text.includes("AUTH_TOKEN"), false);
  assert.match(text, /validateChatResponse/);
  assert.match(text, /generationStatus === "model_generated"/);
  assert.equal(text.includes("rawResponseBody"), false);
});

test("nightly preserves exact production-release and CrossFire controls", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-multi-agent-research-v3.yml"), "utf8");
  for (const token of [
    "heroic-ai-production-release.yml", ".headBranch", '= "main"', "TARGET_FOUNDATION_SHA",
    "RELEASE_RUN_ID", "gh run view", "workflowName", "headSha", "conclusion",
    "select(.name == \"Canonical Heroic AI production release\")",
    "select(.name == \"Run canonical production release\")",
    "timeout-minutes: 5", "short reconciliation", "seq 1 12",
    "name: Nightly research CrossFire (24-program global scheduler)",
    '--crossfire --global-capacity "$RESEARCH_MAX_CONCURRENCY"',
  ]) assert.ok(text.includes(token), token);
  assert.equal(text.includes("workflow_run:"), false);
  assert.equal(text.includes("seq 1 240"), false);
});

test("production release explicitly requests live nightly mode", () => {
  const release = fs.readFileSync(path.join(ROOT, ".github/workflows/heroic-ai-production-release.yml"), "utf8");
  for (const token of [
    "Preflight exact nightly runtime before research dispatch",
    "--field dry_run=false",
    '--field target_sha="$GITHUB_SHA"',
    '--field production_release_run_id="$GITHUB_RUN_ID"',
    "gh workflow run nightly-multi-agent-research-v3.yml",
  ]) assert.ok(release.includes(token), token);
  assert.equal(release.includes("dry_run:false"), false);
});

test("private Operations pin and permissions remain explicit", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-multi-agent-research-v3.yml"), "utf8");
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT, "docs/OPERATIONS_PIN_MANIFEST.json"), "utf8"));
  const researchPin = manifest.pins.research_runtime.sha;
  for (const token of [
    "OPERATIONS_RESEARCH_REF:", researchPin,
    "private.multi_agent.runner",
    "OPERATIONS_APP_ID: " + "$" + "{{ secrets.OPERATIONS_APP_ID }}",
    "OPERATIONS_APP_PRIVATE_KEY: " + "$" + "{{ secrets.OPERATIONS_APP_PRIVATE_KEY }}",
  ]) assert.ok(text.includes(token), token);
  assert.equal(text.includes("OPERATIONS_READ_TOKEN"), false);
  const top = text.split("jobs:", 1)[0];
  assert.equal(top.includes("id-token: write"), false);
  assert.equal(top.includes("attestations: write"), false);
});

test("nightly structured contract, coverage and acceptance gates remain present", () => {
  const text = fs.readFileSync(path.join(ROOT, ".github/workflows/nightly-multi-agent-research-v3.yml"), "utf8");
  for (const token of [
    "nightly-research-contract/v2", "fromjson", 'has("findings")',
    'has("follow_up_questions")', 'has("note")', "max_tokens:96",
    "nightly-research-coverage/v1", "expected_program_count", "missing_program_ids",
    "unexpected_program_ids", "duplicate_program_ids",
    "nightly-research-acceptance-requirements/v1", "'foundation_58'", "'foundation_157'",
    "'operations_597'", "'operations_603'", "pending_external_runtime",
    "'cases'", "'repeats_min'", "shadow", "canary", "rollback",
  ]) assert.ok(text.includes(token), token);
});

test("Node proxy preserves bounded recovery and request proof requirements", () => {
  const proxy = fs.readFileSync(path.join(ROOT, "scripts/research_worker_proxy.mjs"), "utf8");
  for (const token of [
    "MAX_UPSTREAM_ATTEMPTS = 3", "RETRYABLE_UPSTREAM_STATUS",
    "retry-after", "bounded_3_attempts", '"X-Heroic-Research-Proof: 1"',
    "MAX_BODY_BYTES", "MAX_QUEUE_WAIT_SECONDS", "require_model_generation: true",
  ]) assert.ok(proxy.includes(token), token);
  assert.equal(proxy.includes('"research_agent": true'), false);
});

test("Node probe enforces model-generated structured output", () => {
  const payload = {
    ok: true,
    response: {
      response_id: "probe",
      provider: "cloudflare_workers_ai",
      generation_status: "model_generated",
      text: JSON.stringify({ findings: [], follow_up_questions: [], note: "probe" }),
    },
  };
  const [ok] = validateChatResponse(payload, "@cf/zai-org/glm-4.7-flash");
  assert.equal(ok, true);
  const fallback = {
    ok: true,
    response: {
      response_id: "probe",
      generation_status: "deterministic_fallback",
      text: JSON.stringify({ findings: [], follow_up_questions: [], note: "fallback" }),
    },
  };
  const [fallbackOk] = validateChatResponse(fallback, "@cf/zai-org/glm-4.7-flash");
  assert.equal(fallbackOk, false);
});
