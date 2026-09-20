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
  assert.throws(
    () => assertPublicDestination(
      "https://example.com/products",
      { allowed: true, addresses: ["127.0.0.1"] },
    ),
    /non-public/,
  );
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
