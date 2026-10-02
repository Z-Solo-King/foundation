import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { validateChatResponse } from "../scripts/nightly_runtime_contract_probe.mjs";

const ROOT = path.resolve(new URL("..", import.meta.url));

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
