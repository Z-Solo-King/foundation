export type EdgeStatus =
  | "ok"
  | "ready"
  | "unsupported"
  | "error";

export interface EdgeEnvelope<T = unknown> {
  ok: boolean;
  status: EdgeStatus;
  data?: T;
  error?: string;
  contract_version: "public-edge-shadow/v1";
}

export interface EdgeEnvironment {
  environment?: string;
  operations?: {
    fetch(request: Request): Promise<Response>;
  };
}

export function healthResponse(env: EdgeEnvironment = {}): Response {
  const body: EdgeEnvelope = {
    ok: true,
    status: "ok",
    contract_version: "public-edge-shadow/v1",
    data: {
      service: "research-intelligence-engine-public",
      runtime: "typescript-shadow",
      environment: env.environment ?? "unknown",
    },
  };
  return Response.json(body, { status: 200 });
}

export function readinessResponse(env: EdgeEnvironment = {}): Response {
  const ready = Boolean(env.operations);
  const body: EdgeEnvelope = {
    ok: ready,
    status: ready ? "ready" : "error",
    contract_version: "public-edge-shadow/v1",
    ...(ready ? {} : { error: "operations service binding unavailable" }),
  };
  return Response.json(body, { status: ready ? 200 : 503 });
}

export async function handleShadow(
  request: Request,
  env: EdgeEnvironment = {},
): Promise<Response> {
  const url = new URL(request.url);

  if (request.method === "GET" && url.pathname === "/health") {
    return healthResponse(env);
  }

  if (request.method === "GET" && url.pathname === "/readiness") {
    return readinessResponse(env);
  }

  return Response.json(
    {
      ok: false,
      status: "unsupported" satisfies EdgeStatus,
      contract_version: "public-edge-shadow/v1",
      error: "shadow route not yet migrated",
    } satisfies EdgeEnvelope,
    { status: 404 },
  );
}
