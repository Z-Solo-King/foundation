function isBackendPath(pathname) {
  return pathname === "/health" ||
    pathname === "/readiness" ||
    pathname.startsWith("/api/");
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (isBackendPath(url.pathname)) {
      return env.HEROIC_BACKEND.fetch(request);
    }

    const assetResponse = await env.ASSETS.fetch(request);
    if (assetResponse.status !== 404) {
      return assetResponse;
    }

    if (request.method === "GET") {
      return env.ASSETS.fetch(new Request(new URL("/", request.url), request));
    }

    return assetResponse;
  },
};
