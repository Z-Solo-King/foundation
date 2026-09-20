export const MAX_PUBLIC_REDIRECTS = 3;
export const MAX_PUBLIC_RESPONSE_BYTES = 1_000_000;
export const PUBLIC_HTTP_METHOD = "GET" as const;

export interface PublicDestinationDecision {
  allowed: boolean;
  addresses?: string[];
  reason?: string;
}

export interface PublicFetchResponse {
  status: number;
  headers: Record<string, string>;
  body: Uint8Array;
  finalUrl: string;
  redirectChain: string[];
}

function hostname(url: URL): string {
  const value = url.hostname.toLowerCase().replace(/\.$/, "");
  if (!value) throw new Error("target host is required");
  return value;
}

export function canonicalizePublicUrl(input: string): string {
  const url = new URL(input);
  if (!["http:", "https:"].includes(url.protocol)) throw new Error("only http and https URLs are allowed");
  if (url.username || url.password) throw new Error("userinfo in URL is not allowed");
  if (![80, 443, 0].includes(url.port ? Number(url.port) : 0)) throw new Error("non-standard ports are not allowed");
  url.hostname = hostname(url);
  url.hash = "";
  if (!url.pathname) url.pathname = "/";
  return url.toString();
}

export function assertPublicDestination(input: string, decision: PublicDestinationDecision): void {
  canonicalizePublicUrl(input);
  if (!decision.allowed) throw new Error(decision.reason ?? "target host is not allowed");
}

export function nextRedirect(
  currentUrl: string,
  location: string,
  redirects: number,
  originalScheme: "http:" | "https:",
): string {
  if (redirects >= MAX_PUBLIC_REDIRECTS) throw new Error("too many redirects");
  const next = new URL(location, currentUrl);
  const canonical = canonicalizePublicUrl(next.toString());
  if (originalScheme === "https:" && new URL(canonical).protocol !== "https:") {
    throw new Error("https to http redirect downgrade is not allowed");
  }
  return canonical;
}

export function acceptPublicResponse(response: {
  status: number;
  headers: Record<string, string>;
  body: Uint8Array;
  finalUrl: string;
  redirectChain: string[];
}): PublicFetchResponse {
  if (response.body.byteLength > MAX_PUBLIC_RESPONSE_BYTES) {
    throw new Error("response exceeds acquisition size budget");
  }
  return {
    status: response.status,
    headers: { ...response.headers },
    body: response.body,
    finalUrl: canonicalizePublicUrl(response.finalUrl),
    redirectChain: [...response.redirectChain],
  };
}
