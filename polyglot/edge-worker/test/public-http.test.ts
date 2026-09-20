import assert from "node:assert/strict";
import { test } from "node:test";
import {
  MAX_PUBLIC_REDIRECTS,
  MAX_PUBLIC_RESPONSE_BYTES,
  acceptPublicResponse,
  assertPublicDestination,
  canonicalizePublicUrl,
  nextRedirect,
} from "../src/public-http.ts";

test("canonicalizes public HTTP URLs without userinfo or fragments", () => {
  assert.equal(
    canonicalizePublicUrl("HTTPS://Example.COM:443/products#fragment"),
    "https://example.com/products",
  );
  assert.throws(
    () => canonicalizePublicUrl("https://user:pass@example.com/products"),
    /userinfo/,
  );
  assert.throws(
    () => canonicalizePublicUrl("https://example.com:8443/products"),
    /non-standard/,
  );
});

test("trusts Python-owned DNS decision instead of implementing a second resolver", () => {
  assert.doesNotThrow(() => assertPublicDestination(
    "https://example.com/products",
    { allowed: true, addresses: ["93.184.216.34"] },
  ));
  assert.doesNotThrow(() => assertPublicDestination(
    "https://example.com/products",
    { allowed: true, addresses: ["127.0.0.1"] },
  ));
  assert.throws(
    () => assertPublicDestination(
      "https://example.com/products",
      { allowed: false, reason: "DNS authority unavailable" },
    ),
    /DNS authority unavailable/,
  );
});

test("preserves HTTPS and bounds redirects", () => {
  assert.equal(
    nextRedirect("https://example.com/products", "/page-2", 0, { originalScheme: "https:" }),
    "https://example.com/page-2",
  );
  assert.throws(
    () => nextRedirect("https://example.com/products", "http://example.com/page-2", 0, { originalScheme: "https:" }),
    /downgrade/,
  );
  assert.throws(
    () => nextRedirect("https://example.com/products", "/page-4", MAX_PUBLIC_REDIRECTS, { originalScheme: "https:" }),
    /too many redirects/,
  );
});

test("bounds fetched response size and preserves response provenance", () => {
  const body = new Uint8Array([1, 2, 3]);
  const result = acceptPublicResponse({
    status: 200,
    headers: { "content-type": "application/json" },
    body,
    finalUrl: "https://example.com/products",
    redirectChain: ["https://example.com/products"],
  });
  assert.equal(result.status, 200);
  assert.deepEqual(Array.from(result.body), [1, 2, 3]);
  assert.deepEqual(result.redirectChain, ["https://example.com/products"]);
  assert.throws(
    () => acceptPublicResponse({
      status: 200,
      headers: {},
      body: new Uint8Array(MAX_PUBLIC_RESPONSE_BYTES + 1),
      finalUrl: "https://example.com/products",
      redirectChain: [],
    }),
    /acquisition size budget/,
  );
});


test("canonicalization accepts only standard HTTP(S) destinations", () => {
  const cases = [
    ["https://EXAMPLE.com:443/a#x", "https://example.com/a"],
    ["http://example.com:80/a", "http://example.com/a"],
    ["https://example.com/a?x=1#fragment", "https://example.com/a?x=1"],
    ["http://example.com", "http://example.com/"],
  ];
  for (const [input, expected] of cases) assert.equal(canonicalizePublicUrl(input), expected);
});

test("destination decision remains the external security authority", () => {
  assert.doesNotThrow(() => assertPublicDestination("https://example.com/", { allowed: true, addresses: ["127.0.0.1"] }));
  assert.throws(() => assertPublicDestination("https://example.com/", { allowed: false, reason: "private destination" }), /private destination/);
});

test("redirect and body limits remain deterministic at their exact boundaries", () => {
  assert.doesNotThrow(() => nextRedirect("https://example.com/", "/one", MAX_PUBLIC_REDIRECTS - 1, { originalScheme: "https:" }));
  assert.throws(() => nextRedirect("https://example.com/", "/two", MAX_PUBLIC_REDIRECTS, { originalScheme: "https:" }), /too many redirects/);
  assert.doesNotThrow(() => acceptPublicResponse({ status: 200, headers: {}, body: new Uint8Array(MAX_PUBLIC_RESPONSE_BYTES), finalUrl: "https://example.com/", redirectChain: [] }));
});
