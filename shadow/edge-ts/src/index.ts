export interface ShadowEnv {
  ENVIRONMENT?: string;
  VERSION?: string;
  APP_NAME?: string;
  DB?: D1Database;
}

export interface HealthPayload {
  ok: boolean;
  status: string;
  app: string;
  version: string;
  environment: string;
}

export interface ReadinessPayload {
  ready: boolean;
  version: string;
  database: boolean;
}

function json(payload: unknown, status = 200): Response {
  return new Response(JSON.stringify(payload), {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "private, no-store, max-age=0, must-revalidate",
    },
  });
}

async function health(env: ShadowEnv): Promise<Response> {
  const body: HealthPayload = {
    ok: true,
    status: "ok",
    app: env.APP_NAME ?? "research-intelligence-engine",
    version: env.VERSION ?? "shadow",
    environment: env.ENVIRONMENT ?? "",
  };
  return json(body);
}

async function readiness(env: ShadowEnv): Promise<Response> {
  const version = env.VERSION ?? "shadow";
  if (!env.DB) {
    return json({ ready: false, version, database: false } satisfies ReadinessPayload, 503);
  }

  try {
    const row = await env.DB.prepare("SELECT 1 AS ok").first<{ ok: number }>();
    const database = row?.ok === 1;
    return json({ ready: database, version, database } satisfies ReadinessPayload, database ? 200 : 503);
  } catch {
    return json({ ready: false, version, database: false } satisfies ReadinessPayload, 503);
  }
}

export default {
  async fetch(request: Request, env: ShadowEnv): Promise<Response> {
    const url = new URL(request.url);

    switch (url.pathname) {
      case "/health":
        return health(env);
      case "/readiness":
        return readiness(env);
      default:
        return json({ ok: false, error: "not_found" }, 404);
    }
  },
};
