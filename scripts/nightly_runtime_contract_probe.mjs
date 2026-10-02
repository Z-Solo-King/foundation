#!/usr/bin/env node
/** Probe the exact deployed public Worker contract used by nightly CrossFire. */
import { randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";

function parseArgs(argv) {
  const out = {};
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith("--")) continue;
    out[key.slice(2)] = argv[i + 1] ?? "";
    i += 1;
  }
  return out;
}

async function readLimited(response, maxBytes) {
  if (!response.body) return "";
  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    total += value.byteLength;
    if (total > maxBytes) {
      await reader.cancel().catch(() => {});
      throw new Error("response exceeds supported size");
    }
    chunks.push(Buffer.from(value));
  }
  return Buffer.concat(chunks).toString("utf8");
}

async function jsonRequest(url, options, maxBytes) {
  try {
    const response = await fetch(url, {
      ...options,
      signal: AbortSignal.timeout(options.timeoutMs ?? 30_000),
    });
    const raw = await readLimited(response, maxBytes);
    let body = {};
    try { body = raw ? JSON.parse(raw) : {}; } catch { body = {}; }
    return { status: response.status, body: body && typeof body === "object" && !Array.isArray(body) ? body : {} };
  } catch {
    return { status: 0, body: {} };
  }
}

export function validateChatResponse(payload, expectedModel = "") {
  const response = payload?.response;
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    return [false, {
      response_id_present: false,
      provider_present: false,
      generation_status: null,
      structured_output: false,
    }];
  }
  const provider = response.provider;
  const responseId = response.response_id;
  const generationStatus = response.generation_status;
  const text = response.text;
  const model = response.model;
  let structured = null;
  if (typeof text === "string" && text.trim()) {
    try { structured = JSON.parse(text); } catch { structured = null; }
  }
  const modelOk = model == null || !expectedModel || model === expectedModel;
  const details = {
    response_id_present: typeof responseId === "string" && Boolean(responseId.trim()),
    provider_present: typeof provider === "string" && Boolean(provider.trim()),
    provider: typeof provider === "string" ? provider : null,
    generation_status: typeof generationStatus === "string" ? generationStatus : null,
    model_present: typeof model === "string" && Boolean(model.trim()),
    model_match: modelOk,
    structured_output: Boolean(structured && typeof structured === "object" && !Array.isArray(structured)),
  };
  const ok =
    payload?.ok === true &&
    details.response_id_present &&
    details.provider_present &&
    generationStatus === "model_generated" &&
    typeof text === "string" &&
    Boolean(text.trim()) &&
    details.structured_output &&
    Array.isArray(structured.findings) &&
    Array.isArray(structured.follow_up_questions) &&
    typeof structured.note === "string" &&
    modelOk;
  return [ok, details];
}

export async function main() {
  const args = parseArgs(process.argv.slice(2));
  const url = args.url;
  const token = args.token;
  const model = args.model;
  if (!url || !token || !model) throw new Error("--url, --token and --model are required");

  const base = url.replace(//+$/, "");
  const readiness = await jsonRequest(base + "/readiness", {
    method: "GET",
    headers: {
      Accept: "application/json",
      "User-Agent": "HeroicNightlyResearchContract/2026.09",
      Connection: "close",
    },
    timeoutMs: 30_000,
  }, 500_001);

  const release = readiness.body?.release && typeof readiness.body.release === "object" ? readiness.body.release : {};
  const readinessOk =
    readiness.status === 200 &&
    readiness.body?.ready === true &&
    readiness.body?.database === true &&
    (!args["expected-foundation-sha"] || release.foundation_sha === args["expected-foundation-sha"]) &&
    (!args["expected-operations-ref"] || release.operations_ref === args["expected-operations-ref"]);

  const requestId = "nightly-contract-probe-" + randomUUID().replaceAll("-", "");
  const requestBody = {
    chat_id: requestId,
    request_id: requestId,
    message: "Return the smallest valid research object with findings as an empty array, follow_up_questions as an empty array, and note as probe.",
    mode: "chat",
    operation: "knowledge",
    strict_zero_cost_only: true,
    require_model_generation: true,
  };

  let chatStatus = 0;
  let payload = {};
  if (readinessOk) {
    const chat = await jsonRequest(base + "/api/v1/chat", {
      method: "POST",
      headers: {
        Authorization: "Bearer " + token,
        "Content-Type": "application/json",
        "Idempotency-Key": requestId,
        "X-Heroic-Research-Proof": "1",
        "User-Agent": "HeroicNightlyResearchContract/2026.09",
        Accept: "application/json",
        "Accept-Encoding": "identity",
        Connection: "close",
      },
      body: JSON.stringify(requestBody),
      timeoutMs: 90_000,
    }, 2_000_001);
    chatStatus = chat.status;
    payload = chat.body;
  }

  const [chatValidated, chatDetails] = validateChatResponse(payload, model);
  const chatOk = chatStatus === 200 && chatValidated;
  const ok = readinessOk && chatOk;
  const classification = ok
    ? "accepted_exact_research_contract"
    : !readinessOk
      ? (readiness.status === 200 && Object.keys(release).length ? "runtime_revision_mismatch" : "readiness_failure")
      : chatStatus === 0
        ? "probe_transport_error"
        : !Object.keys(payload).length
          ? "invalid_json_response"
          : "research_contract_rejected";

  if (!ok) {
    process.stdout.write(JSON.stringify({
      probe_failure_diagnostics: {
        readiness_status: readiness.status,
        readiness_release: release,
        expected_foundation_sha: args["expected-foundation-sha"] || "",
        expected_operations_ref: args["expected-operations-ref"] || "",
        chat_status: chatStatus,
        chat_details: chatDetails,
      },
    }) + "\n");
  }

  process.stdout.write(JSON.stringify({
    schema: "nightly-runtime-contract-probe/v2",
    ok,
    classification,
    readiness_http_status: readiness.status,
    readiness_ready: readiness.body?.ready === true,
    readiness_database: readiness.body?.database === true,
    deployed_foundation_sha: release.foundation_sha,
    deployed_operations_ref: release.operations_ref,
    expected_foundation_sha: args["expected-foundation-sha"] || "",
    expected_operations_ref: args["expected-operations-ref"] || "",
    chat_http_status: chatStatus,
    expected_model: model,
    ...chatDetails,
    request_contract: {
      operation: "knowledge",
      proof_header: true,
      require_model_generation: true,
    },
    probe_timestamp_unix: Math.floor(Date.now() / 1000),
  }) + "\n");
  process.exitCode = ok ? 0 : 1;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  main().catch((error) => {
    process.stderr.write(String(error?.message || error) + "\n");
    process.exitCode = 1;
  });
}
