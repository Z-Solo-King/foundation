interface ServiceBinding {
  fetch(request: Request): Promise<Response>;
}

interface EdgeEnv {
  CORE?: ServiceBinding;
}

function forwardRequest(request: Request): Request {
  const incoming = new URL(request.url);
  const target = new URL("https://heroic-core");
  target.pathname = incoming.pathname;
  target.search = incoming.search;
  return new Request(target, request.clone());
}

function unavailableResponse(): Response {
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

const handler = {
  async fetch(request: Request, env: EdgeEnv): Promise<Response> {
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
