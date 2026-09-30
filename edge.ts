/**
 * Typed public edge facade for Heroic AI.
 *
 * The edge owns only transport and service-binding failure handling. The
 * Python worker remains the application/research authority behind CORE.
 */

/** @typedef {{ fetch(request: Request): Promise<Response> }} ServiceBinding */
/** @typedef {{ CORE?: ServiceBinding }} EdgeEnv */

/** @param {Request} request */
function forwardRequest(request) {
  const incoming = new URL(request.url);
  const target = new URL("https://heroic-core");
  target.pathname = incoming.pathname;
  target.search = incoming.search;
  return new Request(target, request.clone());
}

function unavailableResponse() {
  return new Response(
    JSON.stringify({ ok: false, error: "core_service_unavailable" }),
    {
      status: 503,
      headers: {
        "Content-Type": "application/json; charset=utf-8",
        "Cache-Control": "no-store",
      },
    },
  );
}

/** @type {{ fetch(request: Request, env: EdgeEnv): Promise<Response> }} */
const handler = {
  async fetch(request, env) {
    if (!env.CORE || typeof env.CORE.fetch !== "function") {
      return unavailableResponse();
    }

    try {
      return await env.CORE.fetch(forwardRequest(request));
    } catch (error) {
      console.error("heroic core service binding failure", error);
      return unavailableResponse();
    }
  },
};

export default handler;
