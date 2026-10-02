#!/usr/bin/env node
/**
 * Loopback OpenAI-compatible adapter for nightly research.
 *
 * The CI runner cannot use the private Operations service binding directly.
 * This adapter keeps the research executor contract unchanged while routing
 * requests through the authenticated production-safe Foundation Worker.
 *
 * Only 127.0.0.1 is served. The CI bearer token is never logged.
 */
import http from "node:http";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { createHash, randomUUID } from "node:crypto";

const execFileAsync = promisify(execFile);

const MAX_BODY_BYTES = 131_072;
const MAX_MESSAGE_CHARS = 11_800;
const UPSTREAM_USER_AGENT = "HeroicAI-NightlyResearch/1.1";
const DEFAULT_MAX_UPSTREAM_CONCURRENCY = 6;
const MAX_QUEUE_WAIT_SECONDS = 180;
const MAX_UPSTREAM_ATTEMPTS = 3;
const RETRYABLE_UPSTREAM_STATUS = new Set([408, 429, 500, 502, 503, 504]);
const RETRY_BASE_DELAY_SECONDS = 1;
const RETRY_MAX_DELAY_SECONDS = 8;

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

function compactMessages(messages) {
  if (!Array.isArray(messages) || messages.length === 0) {
    throw new Error("messages must be a non-empty list");
  }
  const systemParts = [];
  const conversationParts = [];
  for (const item of messages) {
    if (!item || typeof item !== "object") continue;
    const role = String(item.role ?? "").trim().toLowerCase();
    const content = item.content;
    if (typeof content !== "string" || !content.trim()) continue;
    const normalized = content.trim();
    if (role === "system") systemParts.push(normalized);
    else conversationParts.push((role || "user") + ": " + normalized);
  }
  if (conversationParts.length === 0) {
    throw new Error("messages contain no usable user content");
  }
  const sections = [];
  if (systemParts.length) {
    sections.push("Research execution instructions:\n" + systemParts.join("\n\n"));
  }
  sections.push("Research request:\n" + conversationParts.join("\n\n"));
  return sections.join("\n\n").trim().slice(0, MAX_MESSAGE_CHARS);
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
      throw new Error("upstream response exceeds supported size");
    }
    chunks.push(value);
  }
  return Buffer.concat(chunks.map((x) => Buffer.from(x))).toString("utf8");
}

async function safeJsonResponse(response, maxBytes) {
  const raw = await readLimited(response, maxBytes);
  try {
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function safeHeaderDetails(headers) {
  const details = {};
  for (const [source, target, limit] of [
    ["server", "upstream_server", 80],
    ["cf-ray", "cf_ray", 120],
    ["cf-mitigated", "cf_mitigated", 80],
    ["retry-after", "retry_after", 40],
  ]) {
    const value = headers?.get?.(source);
    if (typeof value === "string" && value.trim()) details[target] = value.trim().slice(0, limit);
  }
  return details;
}

function safeUpstreamErrorDetails(status, body, headers) {
  const details = { upstream_status: Number(status) || 0 };
  if (body && typeof body === "object") {
    const error = body.error;
    if (typeof error === "string" && error.trim()) {
      details.upstream_error = error.trim().slice(0, 200);
    }
    const response = body.response;
    if (response && typeof response === "object") {
      if (typeof response.generation_status === "string" && response.generation_status.trim()) {
        details.upstream_generation_status = response.generation_status.trim().slice(0, 80);
      }
      if (typeof response.provider === "string" && response.provider.trim()) {
        details.upstream_provider = response.provider.trim().slice(0, 120);
      }
    }
  }
  Object.assign(details, safeHeaderDetails(headers));
  return details;
}

function retryDelaySeconds(headers, attempt) {
  const raw = headers?.get?.("retry-after");
  const value = raw === null || raw === undefined ? Number.NaN : Number.parseFloat(raw);
  if (Number.isFinite(value) && value >= 0) return Math.min(RETRY_MAX_DELAY_SECONDS, value);
  return Math.min(RETRY_MAX_DELAY_SECONDS, RETRY_BASE_DELAY_SECONDS * (2 ** Math.max(0, attempt - 1)));
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function curlPost(url, payload, authToken, requestId) {
  try {
    const args = [
      "-sS", "--max-time", "90", "-X", "POST",
      "-H", "Authorization: Bearer " + authToken,
      "-H", "Accept: application/json",
      "-H", "Content-Type: application/json",
      "-H", "Idempotency-Key: " + requestId,
      "-H", "X-Heroic-Research-Proof: 1",
      "-H", "User-Agent: " + UPSTREAM_USER_AGENT,
      "--data-binary", "@-", "--write-out", "\n%{http_code}", url,
    ];
    const { stdout, stderr } = await execFileAsync("curl", args, {
      input: payload,
      maxBuffer: MAX_BODY_BYTES + 1_024,
      encoding: "buffer",
    });
    const output = Buffer.isBuffer(stdout) ? stdout : Buffer.from(String(stdout));
    const split = output.lastIndexOf(0x0a);
    let body = output;
    let status = 0;
    if (split >= 0) {
      body = output.subarray(0, split);
      status = Number.parseInt(output.subarray(split + 1).toString("utf8").trim() || "0", 10) || 0;
    }
    return { status, body, error: String(stderr || "").trim().slice(0, 240) };
  } catch (error) {
    const stdout = Buffer.isBuffer(error?.stdout) ? error.stdout : Buffer.from(String(error?.stdout || ""));
    const split = stdout.lastIndexOf(0x0a);
    let body = stdout;
    let status = 0;
    if (split >= 0) {
      body = stdout.subarray(0, split);
      status = Number.parseInt(stdout.subarray(split + 1).toString("utf8").trim() || "0", 10) || 0;
    }
    return {
      status,
      body,
      error: String(error?.stderr || error?.message || "").trim().slice(0, 240) || ("curl_exit_" + String(error?.code || "unknown")),
    };
  }
}

class Semaphore {
  constructor(size) {
    this.available = size;
    this.waiters = [];
  }
  async acquire(timeoutMs) {
    if (this.available > 0) {
      this.available -= 1;
      return () => this.release();
    }
    return new Promise((resolve, reject) => {
      const waiter = { resolve, reject, timer: null };
      waiter.timer = setTimeout(() => {
        const index = this.waiters.indexOf(waiter);
        if (index >= 0) this.waiters.splice(index, 1);
        reject(new Error("research_proxy_capacity_queue_timeout"));
      }, timeoutMs);
      this.waiters.push(waiter);
    });
  }
  release() {
    const next = this.waiters.shift();
    if (next) {
      clearTimeout(next.timer);
      next.resolve(() => this.release());
      return;
    }
    this.available += 1;
  }
}

async function readRequestBody(req) {
  const chunks = [];
  let total = 0;
  for await (const chunk of req) {
    const buffer = Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk);
    total += buffer.length;
    if (total > MAX_BODY_BYTES) {
      throw Object.assign(new Error("request_too_large"), { statusCode: 413 });
    }
    chunks.push(buffer);
  }
  if (total <= 0) throw Object.assign(new Error("request_too_large"), { statusCode: 413 });
  return Buffer.concat(chunks).toString("utf8");
}

function sendJson(res, payload, status = 200) {
  const encoded = Buffer.from(JSON.stringify(payload));
  res.writeHead(status, {
    "Content-Type": "application/json",
    "Content-Length": String(encoded.length),
    "Cache-Control": "no-store",
  });
  res.end(encoded);
}

async function handleRequest(req, res, server) {
  if (req.method === "GET" && req.url === "/health") {
    sendJson(res, { ok: true, service: "research-worker-proxy" });
    return;
  }
  if (req.method !== "POST" || req.url !== "/chat/completions") {
    sendJson(res, { ok: false, error: "not_found" }, 404);
    return;
  }
  if (req.headers.authorization !== "Bearer local-worker-proxy") {
    sendJson(res, { ok: false, error: "unauthorized" }, 401);
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(await readRequestBody(req));
    const model = String(parsed?.model ?? "").trim();
    if (!model) throw new Error("model is required");
    const message = compactMessages(parsed?.messages);
    parsed = { model, message };
  } catch (error) {
    sendJson(res, {
      ok: false,
      error: "invalid_request",
      detail: String(error?.message || error).slice(0, 200),
    }, Number(error?.statusCode) || 400);
    return;
  }

  const requestId = "research-proxy-" + randomUUID().replaceAll("-", "");
  const requestDigest = createHash("sha256").update(requestId, "utf8").digest("hex").slice(0, 16);
  const upstreamPayload = {
    chat_id: requestId,
    request_id: requestId,
    message: parsed.message,
    mode: "chat",
    operation: "knowledge",
    strict_zero_cost_only: true,
    require_model_generation: true,
  };
  const upstreamUrl = server.publicWorkerUrl.replace(/\/+$/, "") + "/api/v1/chat";
  const upstreamBody = JSON.stringify(upstreamPayload);

  const started = Date.now();
  let release;
  try {
    release = await server.semaphore.acquire(MAX_QUEUE_WAIT_SECONDS * 1000);
  } catch {
    sendJson(res, {
      error: {
        message: "research_proxy_capacity_queue_timeout",
        type: "backpressure_timeout",
      },
      request_id: requestDigest,
    }, 429);
    return;
  }
  const queueWaitMs = Number((Date.now() - started).toFixed(3));
  let attemptCount = 0;
  let transportUsed = "fetch";
  let lastError = {};
  let body = null;
  let status = 0;

  try {
    for (let attempt = 1; attempt <= MAX_UPSTREAM_ATTEMPTS; attempt += 1) {
      attemptCount = attempt;
      try {
        const response = await fetch(upstreamUrl, {
          method: "POST",
          headers: {
            Authorization: "Bearer " + server.authToken,
            "Content-Type": "application/json",
            "Idempotency-Key": requestId,
            "X-Heroic-Research-Proof": "1",
            "User-Agent": UPSTREAM_USER_AGENT,
            Accept: "application/json",
            "Accept-Encoding": "identity",
            Connection: "close",
          },
          body: upstreamBody,
          signal: AbortSignal.timeout(90_000),
        });
        const candidate = await safeJsonResponse(response, 2_000_001);
        status = response.status;
        if (response.ok) {
          body = candidate;
          break;
        }
        lastError = safeUpstreamErrorDetails(response.status, candidate, response.headers);
        if (response.status === 403) {
          transportUsed = "curl";
          const fallback = await curlPost(upstreamUrl, Buffer.from(upstreamBody), server.authToken, requestId);
          if (fallback.status === 200) {
            try {
              body = JSON.parse(fallback.body.toString("utf8"));
              status = 200;
              break;
            } catch {
              sendJson(res, {
                error: { message: "upstream_worker_invalid_curl_response", type: "protocol_error" },
                request_id: requestDigest,
              }, 502);
              return;
            }
          }
          lastError.fallback_transport = "curl";
          lastError.fallback_http_status = fallback.status;
          if (fallback.error) lastError.fallback_transport_error = fallback.error;
          status = fallback.status;
        }
        if (RETRYABLE_UPSTREAM_STATUS.has(status) && attempt < MAX_UPSTREAM_ATTEMPTS) {
          await sleep(retryDelaySeconds(response.headers, attempt) * 1000);
          continue;
        }
        break;
      } catch (error) {
        lastError = {
          type: error?.name || "Error",
          message: String(error?.message || error).slice(0, 200),
        };
        status = 0;
        if (
          attempt < MAX_UPSTREAM_ATTEMPTS &&
          ["AbortError", "TimeoutError", "TypeError"].includes(error?.name)
        ) {
          await sleep(retryDelaySeconds(null, attempt) * 1000);
          continue;
        }
        break;
      }
    }
  } finally {
    release();
  }

  if (status < 200 || status >= 300 || !body || typeof body !== "object" || Array.isArray(body)) {
    const details = {
      ...lastError,
      attempts: attemptCount,
      transport: transportUsed,
      queue_wait_ms: queueWaitMs,
      retry_policy: "bounded_3_attempts",
    };
    sendJson(res, {
      error: { message: "upstream_worker_rejected", type: "upstream_error", ...details },
      request_id: requestDigest,
    }, 502);
    return;
  }

  const response = body.response;
  if (!response || typeof response !== "object" || Array.isArray(response)) {
    sendJson(res, {
      error: { message: "upstream_response_missing", type: "protocol_error" },
    }, 502);
    return;
  }

  const text = response.text;
  if (typeof text !== "string" || !text.trim()) {
    sendJson(res, {
      error: { message: "upstream_model_text_missing", type: "protocol_error" },
    }, 502);
    return;
  }

  if (response.generation_status !== "model_generated" || !response.provider) {
    sendJson(res, {
      error: {
        message: "provider_required_but_unavailable",
        type: "provider_execution_not_proven",
        generation_status: String(response.generation_status ?? "unknown").slice(0, 80),
        provider: String(response.provider ?? "").slice(0, 120),
      },
      request_id: requestDigest,
    }, 502);
    return;
  }

  sendJson(res, {
    id: "research-" + requestId,
    object: "chat.completion",
    model: String(response.model || parsed.model),
    provider: String(response.provider || "cloudflare_workers_ai"),
    execution_id: requestId,
    choices: [{
      index: 0,
      message: { role: "assistant", content: text },
      finish_reason: "stop",
    }],
    usage: response.usage && typeof response.usage === "object" ? response.usage : {},
  });
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const publicWorkerUrl = args["public-worker-url"];
  const authToken = args["auth-token"] || process.env.RESEARCH_PROXY_AUTH_TOKEN || "";
  const bind = args.bind || "127.0.0.1";
  const port = Number.parseInt(args.port || "8765", 10);
  const maxConcurrency = Number.parseInt(
    args["max-upstream-concurrency"] ||
      process.env.RESEARCH_PROXY_MAX_CONCURRENCY ||
      String(DEFAULT_MAX_UPSTREAM_CONCURRENCY),
    10,
  );

  if (!publicWorkerUrl) throw new Error("--public-worker-url is required");
  if (!authToken) throw new Error("research proxy auth token is required");
  if (!Number.isInteger(port) || port < 1 || port > 65_535) throw new Error("invalid port");
  if (!Number.isInteger(maxConcurrency) || maxConcurrency < 1 || maxConcurrency > 20) {
    throw new Error("max upstream concurrency must be between 1 and 20");
  }

  const semaphore = new Semaphore(maxConcurrency);
  const server = http.createServer((req, res) => {
    handleRequest(req, res, { publicWorkerUrl, authToken, semaphore }).catch((error) => {
      if (!res.headersSent) sendJson(res, { ok: false, error: "internal_error" }, 500);
      else res.destroy();
      process.stderr.write(
        "research proxy internal error: " + String(error?.message || error).slice(0, 200) + "\n",
      );
    });
  });

  server.listen(port, bind, () => {
    process.stdout.write(JSON.stringify({
      ok: true,
      bind,
      port,
      service: "research-worker-proxy",
    }) + "\n");
  });

  const shutdown = () => server.close(() => process.exit(0));
  process.on("SIGINT", shutdown);
  process.on("SIGTERM", shutdown);
}

main();
