# WooCommerce V175 Unknown-Cohort Blocker Audit — 2026-09-30

## Scope

This audit covers the current 22-site unresolved WooCommerce Google Merchant cohort on the V175-derived extraction branch. The V175 source remains the technical evidence authority, while repository issue #1247 is the acceptance authority for what can be certified.

### Current acceptance boundary

- Public acquisition only.
- No CAPTCHA solving, Cloudflare challenge bypass, authentication, clearance-cookie replay, or anti-bot bypass.
- A native feed is certified only from the current payload, not from a sitemap, normal RSS/Atom feed, WooCommerce Store API, product REST endpoint, reconstructed XML, or a guessed URL.
- Challenge encounters remain `unverified` rather than `negative`.

## Blocker matrix

| Blocker | Observed state | Root cause | Disposition |
|---|---|---|---|
| Cloudflare Browser Run quota | Account zone is Free Website; Quick Actions are quota-limited | Browser Run Free limits are intentionally small and REST returns 429/2001 when over limit | Disable as default parallel dependency; retain as an explicit, paced diagnostic fallback |
| Cloudflare REST credential | Workflow secret path produced 401 | The current repository environment does not have a usable Browser Run REST token | Do not manufacture or request credentials; use Workers binding/standard public browser lanes instead |
| Cloudflare challenges | Multiple retailers return 403/5xx challenge pages | Target-side bot/challenge policy | Do not bypass; mark evidence blocked and stop native certification for that site |
| Clearance-cookie state | Earlier harness propagated browser cookies between engines and into feed/API probes | Cross-engine state replay can become challenge bypass and violates issue #1247 | Removed from accepted path; browser contexts are independent and direct requests are cookie-free |
| Camoufox / nodriver | Workflow installed stealth/anti-detect tooling but did not need it for compliant verification | These tools can be used for fingerprint/anti-bot evasion | Removed from the extraction workflow; researched only, not an acceptance path |
| Browserless | Optional hosted browser adapter may return rendered pages | External browser can obscure whether a challenge was bypassed | Diagnostic-only; its output cannot certify a native feed |
| Weak XHR visibility | Previous pass focused on selected response URLs/content types | Feed endpoints may be ordinary `admin-ajax.php`, `wc-ajax`, or fetch resources | Capture request URLs plus `performance.getEntriesByType('resource')`; inspect bounded response bodies for feed-like traffic |
| Random CTX feed IDs | CTX Feed may expose a random feed key instead of a fixed filename | Candidate list cannot know the ID a priori | Parse `woo_feed=<id>` and re-test with `wt=xml` |
| Randomized native GPF paths | WooCommerce Google Product Feed can use generated feed endpoints | Fixed-only probing misses configured/random paths | Mine explicit href/src/loc and historical URLs; validate only current payload |
| Historical URL drift | Wayback/Common Crawl can expose stale feed URLs | Old feed may disappear or change | Historical URLs are candidate hints only; current request must pass strict native validation |
| Sitemaps/robots | Valuable passive source, not guaranteed feed source | Feed URLs can be referenced indirectly | Probe robots and sitemap surfaces and harvest feed-like URLs without treating the sitemap itself as a Merchant feed |
| GitHub Actions capacity | Initial six-shard run queued behind runner capacity; canonical main run later completed | Runner availability | Keep six shards; canonical run #11 finished successfully; no execution blocker remains |

## Implemented alternative

The extraction path is now a layered pipeline:

1. Clean Chromium + Firefox + WebKit, with no cookie state transferred between engines.
2. Request/XHR/resource URL capture including `admin-ajax.php`, `wc-ajax`, and `performance` resources.
3. Public WordPress API surface checks with no browser-cookie replay.
4. Passive robots/sitemap discovery.
5. Wayback historical candidate discovery; optional Common Crawl discovery remains disabled by default because its public index service is separately rate-limited.
6. Plugin-family fingerprinting with confidence based on evidence provenance.
7. Query-aware CTX/GPF candidate generation.
8. A bounded, cookie-free direct feed probe (40 candidates/site by default).
9. Strict current-payload validation for Google Merchant XML, including RSS `<item>` and Atom `<entry>`.
10. Any challenge encounter makes native verification inadmissible for that site even if another transport happens to return usable content.

## Research conclusions

Cloudflare documents Browser Run Quick Actions through Workers bindings and states that the Worker binding does not need an API token. Cloudflare also documents substantially higher Workers Paid limits, but the current account is Free, so those higher limits do not apply here.

Cloudflare documents session recording with network inspection and a network API. That is useful when a compliant browser session is available for a target that does not present a challenge. It should not be used to evade a challenge.

Cloudflare documents `addScriptTag`, `waitForTimeout`, `waitForSelector`, request/resource filtering, and rendered `/content`, which supports future diagnostic collection without adding another scraper stack.

Official plugin documentation also confirms several public feed conventions used by the candidate miner, including WooCommerce Google Product Feed query feeds, CTX Feed `woo_feed=<id>&wt=xml`, CodeSolz uploads, FeedCraft REST paths, and managed AdTribes feed URLs.

## Result semantics

`native_feed.verified=true` means a current public payload was fetched and passed the strict validator on an admissible, non-challenged path.

`challenge_encountered=true` means the site is blocked for certification in this run. Its plugin hints are diagnostic only.

Historical candidates are never certified solely because an archive contained them.

## Final acceptance result

The improved workflow ran on trusted `main` as run #11 and completed successfully. Its aggregate contains exactly 22 current targets and excludes the known ten. All six shards and the aggregate validator passed. Native-feed verification remains payload-based, and the final aggregate contains 0 verified native Google Merchant feeds and 0 verified feed-generator families for this cohort.

The remaining target-side blockers are therefore genuine public-access limitations (challenge/DNS) rather than CI or extractor execution failures.