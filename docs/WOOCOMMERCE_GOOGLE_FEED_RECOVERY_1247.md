# Public Feed Recovery Methodology — Issue #1247

Date: 2026-09-27

The public Foundation repository retains methodology only. Live retailer identities, target URLs, AI-discovered candidate paths, raw responses and recovery output are maintained on the private Operations surface.

## Method

Recovery candidates may use public native Google Merchant feed paths, public WooCommerce Store API surfaces, adaptive pagination and bounded HTTP/curl fallback.

A result is considered a native Google Merchant feed only when the response contains the Google Merchant namespace plus product item/entry nodes and required merchant fields.

A Store API reconstruction is recorded separately and is never presented as the retailer's native Merchant feed.

## Acquisition modes

The recovery system may select direct HTTP, browser retrieval, public API/feed endpoints, structured page data, or another configured acquisition route for the target. A transport failure is not a feed-negative result; the selected route and resulting evidence must be recorded.

## Evidence boundary

The public repository does not contain the live target registry or target-specific recovery output. Actual recovery remains an evidence-gated private execution task.
