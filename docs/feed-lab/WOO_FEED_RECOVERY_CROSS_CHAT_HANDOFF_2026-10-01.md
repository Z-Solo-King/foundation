# WooCommerce Google XML Feed Recovery — Cross-Chat Handoff — 2026-10-01

## Purpose

Continue the existing WooCommerce Google XML feed recovery work without restarting extraction, plugin crawling, Store API acquisition, or broad blind filename guessing.

The intended pipeline is:

1. Existing public extraction/grouping work identifies plugin/family evidence.
2. Research the plugin family and learn its documented feed URL grammar.
3. Guess/live-probe family-specific Google XML URLs.
4. Validate only a current same-host Google Merchant XML payload.
5. Promote a site to a plugin/feed family only when current evidence supports the family.
6. Only after identified families are exhausted, work on the true unknown-family cohort.
7. For unknowns, use new public evidence (indexed references, Common Crawl, Wayback, code/forum references, newly researched plugin families) to learn a family before expanding URL guesses.

## Canonical repository state

Repository: `Z-Solo-King/foundation`

Current main: `0c1593ce654cce91e4cf6017412a9953a61d7d37`

Canonical acceptance issue: #1247

Related custom/API issue: #1249

Important connector boundary: keep Cloudflare-specific investigation in the separate Cloudflare chat. Share durable state through Foundation issue/docs. Do not duplicate the Cloudflare connector work here.

## What is already completed

### Identified-family gate

PR #1640 was merged. Live Actions run: `36759700843`. Aggregate artifact: `11118179102`.

Seven standalone identified-family targets were exhausted with family-specific grammars:

- PC Studio → WooCommerce Google Product Feed
- Quickin Computers → CTX / WebAppick
- Avikaretails → AdTribes Product Feed PRO
- IT Gadgets Online → Product Feed Manager / WPFM
- Prime ABGB → WooCommerce Google Product Feed
- Kryptronix Gaming → WebToffee Product Feed
- NCL Computer → WebToffee Product Feed

Result: 0/7 current native Google Merchant XML; 2 clean no-hit; 5 transport-limited.

Variety Infotech was demoted back to the unknown cohort because the earlier Google-for-WooCommerce hypothesis was not supported strongly enough by current public plugin evidence.

### True unknown cross-family guessing

PR #1645 was merged.

Live run: `36762779827`.
Aggregate artifact: `11119717351`.

17 true unknown targets:

Aarna Computers; Ads Store; EZPZ Solutions; GamesNComps; hotshiftpc; ithunt; KC Computers; KRG KART; PC Kumar Infotech; PCHubShop; SCL Gaming; Viper PC; Cosmic Byte; Meckeys; StacksKB; Theproaudio; Variety Infotech.

V6 result:
- 0/17 current native Google Merchant XML verified
- 1 clean no-hit
- 16 transport-limited
- 7,468 candidate hypotheses

Important interpretation: transport-limited is not feed absence.

### WPFactory / Alg family

Repository-history research discovered WPFactory / Alg Product XML Feeds with deterministic `/products.xml`.

Micro-wave run: `36762779812`.
Aggregate artifact: `11119592064`.

Result:
- 0/17 native feeds
- 2 clean no-hit
- 15 transport-limited

### SVMPForge family

Repository history discovered SVMPForge Product Feed for WooCommerce.

Documented form:
`/apfw-feed/<unique-token>.xml`

The token is generated/random, so random token enumeration is prohibited and was not used.

PR #1648 merged.
Merge commit: `2c6882da6abc380ebf21d1ef86ee3c46a8eddca2`.

Live run: `36764472477`.
Aggregate artifact: `11120031539`.

Result: 0/17 current native Google Merchant XML; no historical same-host SVMPForge feed references recovered.

## Family inventory currently known

Standalone / XML-capable families researched in the repository:

1. WooCommerce Google Product Feed
2. CTX Feed / WebAppick
3. AdTribes Product Feed PRO
4. Product Feed Manager / WPFM
5. WebToffee
6. CodeSolz Merchant Feed Booster
7. FeedCraft
8. RexFeed
9. KLPSoft
10. iCopyDoc
11. WPFactory / Alg Product XML Feeds
12. SVMPForge Product Feed for WooCommerce

Google for WooCommerce / Google Listings & Ads is treated as an API-integrated architecture and is not forced into standalone XML URL guessing.

## Current open experimental PRs

### PR #1660 — current active lane

Title: `feat: search-index Google XML feed guessing v8`

Branch: `feat/wc-google-feed-index-guess-v8-20261001`

Head: `8c76471d9ddf63868d73c2dac36d69f732643036`

Purpose:
- DuckDuckGo HTML search
- Google web search
- Bing web search
- exact same-host XML/feed candidate extraction
- current re-probe
- strict Merchant XML validation

Run: `36770921960`

At handoff time:
- shard 3: complete
- shard 4: complete
- shard 5: complete
- shard 6: complete
- shard 1: still running
- shard 2: still running

Do NOT start a duplicate public-index run until this one is fully reconciled.

### PR #1656

Historical wildcard Google feed URL recovery v10.
Open, but overlapping with the newer public-index/adaptive work. Treat as experimental/non-authoritative unless its evidence is materially different.

### PR #1657

Common Crawl historical Google feed URL recovery v11.
Open, but overlapping with the newer adaptive/public-index work. Treat as experimental/non-authoritative unless its evidence is materially different.

### PR #1658

Adaptive unknown WooCommerce feed guessing v7.
Open. Uses transport-aware probing, Wayback, Common Crawl, family inference and learned grammars.
Treat as experimental/non-authoritative until the newer public-index lane is reconciled.

### PR #1653

SVMPForge live Google XML guessing v9.
Open but superseded in purpose by the merged SVMPForge historical-reference recovery PR #1648 unless it contains genuinely new evidence.

## Strict acceptance contract

A native Google Merchant feed is verified only if the CURRENT response:

- is HTTP 200;
- remains on the same host after redirects;
- is XML/RSS/Atom-like;
- contains Google Merchant namespace `https://base.google.com/ns/1.0`;
- contains `g:id`, `g:title`, `g:link`, and `g:price` in the same item/entry.

Do NOT promote:
- sitemap XML
- normal RSS/Atom
- Store API JSON
- generic product APIs
- GraphQL catalogs
- reconstructed/synthetic XML
- historical-only URLs
- URL strings found in docs without a current valid payload
- 403/429/challenge/timeout states

Those remain evidence or transport states.

## Security / transport boundary

Allowed:
- public unauthenticated GET;
- public search/index research;
- public Wayback/Common Crawl references;
- current-host re-probing of exact public candidate URLs.

Not allowed:
- CAPTCHA solving;
- Cloudflare challenge bypass;
- authentication bypass;
- clearance-cookie replay;
- proxy rotation/evasion;
- stealth/anti-detect browser;
- random token/ID brute force or permutation enumeration.

## Next-chat execution order

1. First inspect the final result of PR #1660 / run `36770921960`.
2. Extract every URL candidate found by Google/Bing/DDG and classify the URL grammar.
3. If a candidate URL points to a new plugin family, research that family before expanding guesses.
4. Re-probe exact current same-host URLs and apply the strict native validator.
5. Update the family inventory with provenance and confidence.
6. For any family hypothesis with enough evidence, run a bounded family-specific wave across the relevant unknown targets.
7. Close/supersede duplicate experimental PRs once their evidence is incorporated.
8. Continue family discovery using public indexed/code/forum references before any new broad filename expansion.
9. Only stop a site after the current public evidence has been exhausted, and preserve 403/429/challenge as transport-unverified rather than negative.

## High-value research directions

Prioritize:
- exact same-host feed URL references in search results;
- public GitHub code/config references containing retailer-specific feed URLs;
- public forum/blog/support references for a specific retailer + plugin;
- WordPress plugin vendor docs that reveal output paths or URL grammar;
- Common Crawl/Wayback URL patterns that expose deterministic names;
- plugin families not yet in the repository inventory.

For random-token families such as SVMPForge, use historical/indexed references only; never enumerate random tokens.

## What the next chat must NOT do

Do not:
- restart the 30-site plugin extraction;
- restart the WooCommerce Store API extraction;
- replace the guessing phase with Store API work;
- repeat the old 49-path blind filename sweep;
- infer plugin identity solely from a Google Merchant Center page phrase;
- call a historical/sitemap/API URL a native feed.

## User's exact requested goal

The user wants the work continued logically until the remaining websites have their feed-generator/plugin family identified wherever public evidence permits. The sequence is important: finish identified-family work first, then unknown-family research/guessing, and keep learning from each run rather than repeatedly guessing the same URL patterns.
