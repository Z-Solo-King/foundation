import type { EdgeRoute, HttpMethod, RouteMatch } from "./contracts.ts";

function normalizePath(url: string): string {
  return new URL(url).pathname;
}

function match(method: HttpMethod, pathname: string, suffix: string): boolean {
  return method === "GET" && pathname.endsWith(suffix);
}

function post(pathname: string, suffix: string): boolean {
  return pathname.endsWith(suffix);
}

export function matchRoute(request: { method: string; url: string }): RouteMatch {
  const method = request.method.toUpperCase();
  const pathname = normalizePath(request.url);

  if (match("GET", pathname, "/health")) return { route: "health", method: "GET", pathname, requiresAuth: false };
  if (match("GET", pathname, "/readiness")) return { route: "readiness", method: "GET", pathname, requiresAuth: false };
  if (match("GET", pathname, "/api/v1/dashboard")) return { route: "dashboard", method: "GET", pathname, requiresAuth: true };

  if (method === "POST" && post(pathname, "/api/v1/chat/stream")) {
    return { route: "chat_stream", method: "POST", pathname, requiresAuth: true };
  }
  if (method === "POST" && post(pathname, "/api/v1/chat")) {
    return { route: "chat", method: "POST", pathname, requiresAuth: true };
  }
  if (method === "POST" && post(pathname, "/api/v1/chatbot/diagnostic")) {
    return { route: "chatbot_diagnostic", method: "POST", pathname, requiresAuth: true };
  }
  if (method === "POST" && post(pathname, "/api/v1/storage/diagnostic")) {
    return { route: "storage_diagnostic", method: "POST", pathname, requiresAuth: true };
  }
  if (method === "POST" && post(pathname, "/api/v1/research/publish")) {
    return { route: "research_publish", method: "POST", pathname, requiresAuth: true };
  }
  if (method === "GET" && pathname.includes("/api/v1/research/")) {
    return { route: "research_run", method: "GET", pathname, requiresAuth: true };
  }
  if (method === "POST" && post(pathname, "/api/v1/research")) {
    return { route: "research", method: "POST", pathname, requiresAuth: true };
  }

  return {
    route: "not_found",
    method: method === "GET" ? "GET" : "POST",
    pathname,
    requiresAuth: false,
  };
}

export function extractBearerToken(authorization: string | null | undefined): string | null {
  if (!authorization?.startsWith("Bearer ")) return null;
  const token = authorization.slice(7).trim();
  return token || null;
}

export function authenticatedJsonHeaders(): Record<string, string> {
  return {
    "Content-Type": "application/json",
    "Cache-Control": "private, no-store, max-age=0, must-revalidate",
  };
}

export function sseHeaders(): Record<string, string> {
  return {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
    "X-Content-Type-Options": "nosniff",
  };
}

export function responseBodyWithinBound(serialized: string, maxBytes = MAX_PUBLIC_JSON_BODY_BYTES): boolean {
  return new TextEncoder().encode(serialized).byteLength <= maxBytes;
}

const MAX_PUBLIC_JSON_BODY_BYTES = 1_048_576;
