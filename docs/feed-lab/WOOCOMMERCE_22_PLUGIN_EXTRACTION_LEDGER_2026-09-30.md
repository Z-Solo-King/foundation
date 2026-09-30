# WooCommerce Google Feed — 22-Site Plugin Extraction Ledger (2026-09-30)

## Scope

This ledger continues the canonical WooCommerce Google-feed recovery work without repeating the ten retailers whose plugin evidence is already established.

### Explicitly excluded: known 10

1. PC Studio — WooCommerce Google Product Feed
2. quickincomputers — CTX Feed / WebAppick
3. avikaretails — Product Feed PRO / AdTribes
4. Geekbees — Google for WooCommerce
5. Ninja Dog — Google for WooCommerce
6. networkitstore — Google for WooCommerce
7. nexusinfosys — Google for WooCommerce
8. solankienterprises — Google for WooCommerce
9. Only SDD — WooCommerce Google Product Feed; native feed already verified
10. itgadgetsonline — Product Feed Manager (WPFM), identified by public `wpfm/v1` namespace

No new plugin-identification pass should spend acquisition budget on these ten unless new evidence is specifically requested.

## Remaining 22-site target set

Aarna Computers, Ads Store, EZPZ Solutions, GamesNComps, hotshiftpc, ithunt, KC Computers, KRG KART, Kryptronix Gaming, NCL Computer, PCHubShop, Prime ABGB, SCL Gaming, Variety Infotech, Viper PC, AULA India, Cosmic Byte, Meckeys, Moskeys, StacksKB, Theproaudio, and one remaining unresolved retailer slot from the canonical 32-site ledger must be supplied from the latest runtime manifest before execution.

**Important:** the canonical runtime evidence currently records 21 `unknown_woocommerce` plus itgadgetsonline as the one newly identified WPFM site. The source-of-truth site manifest must remain authoritative; this document does not invent a missing retailer name.

## Extraction contract

Plugin identification is evidence-only and must use, in parallel where available:

- Playwright/browser-rendered homepage inspection.
- Homepage XHR/fetch/network response URL capture.
- Public `/wp-json/` discovery.
- WordPress `/wp/v2` REST capability inspection.
- Generic REST root / OPTIONS capability probes.
- WooCommerce REST v1/v2/v3 capability probes without retaining product records.
- Plugin asset URLs, public JS/CSS footprints, and readme/version metadata.
- HTML-only plugin fingerprints when browser/network surfaces are unavailable.

Product records and Store API responses are not persisted as plugin-identification evidence.

## Plugin-family feed inference rules

These are candidate-generation rules, not feed verification.

### WooCommerce Google Product Feed

Primary candidate family:

- `/?woocommerce_gpf=google`
- `/woocommerce_gpf/google`
- bounded `gpf_start/gpf_limit` variants.

Acceptance still requires a live native Google Merchant XML payload.

### CTX Feed / WebAppick

CTX Feed documentation states generated files can be stored under:

`/wp-content/uploads/woo-feed/[format]/[feed-name].[ext]`

and gives Google Shopping XML as an example. It also documents query feeds such as:

`?woo_feed=<name>&wt=xml`

Therefore the correct strategy is to recover an exposed feed name/URL first, then validate it, rather than expanding filename permutations indefinitely.

### Product Feed PRO / AdTribes

Documented generated feeds are static files under:

`/wp-content/uploads/woo-product-feed-pro/`

The feed filename is store/feed specific. Candidate generation should therefore prioritize public feed-name evidence before generic filename guessing.

### Product Feed Manager / WPFM

Public evidence and plugin documentation indicate generated feeds are stored in the `wppfm-feeds` uploads area. Filenames are feed-specific; directory discovery alone is insufficient to claim a feed.

### WebToffee Product Feeds

Public support examples show generated files under:

`/wp-content/uploads/webtoffee_product_feed/`

with names such as `wt_<channel>_Feed.xml`. Filename recovery is therefore useful, but the resulting payload must still pass native validation.

### CodeSolz Merchant Feed Booster

The plugin documents public Google Merchant XML feeds generated into WordPress uploads. Treat `codesolz-feeds` as a family fingerprint/candidate directory only; never promote the directory itself to feed evidence.

### Google for WooCommerce

Google for WooCommerce is an API-sync family, not a traditional public XML-feed family. WooCommerce documentation states that it synchronizes through Google's Content API for Shopping and does not expose a separate feed URL. Do not waste XML-guess budget on a site once this plugin is positively identified unless independent evidence points to another feed plugin.

### FeedCraft / other unknown families

Unknown plugin families remain eligible for bounded generic XML discovery plus evidence-driven candidate generation. A guessed URL is never accepted without payload validation.

## Native-feed acceptance contract

A URL is `verified_native` only when the live response is a retailer-hosted XML/RSS/Atom product feed containing the Google Merchant namespace and required product fields, including:

- `g:id`
- `g:title`
- `g:link`
- `g:price`

The validator must reject:

- WooCommerce Store API output.
- Product REST APIs.
- Product JSON.
- XML sitemaps.
- Ordinary RSS/Atom feeds.
- HTML/challenge pages.
- Reconstructed product XML.

HTTP 401/403/429, browser challenges, and unavailable egress are transport-unverified, not feed-negative.

## 2026-09-30 execution findings

- The repository already contains the multi-method V175-derived plugin recovery lane and native XML guessing layer.
- The latest recorded 22-site recovery identified `itgadgetsonline -> wpfm_product_feed_manager`; the other 21 remained `unknown_woocommerce`.
- The targeted WPFM XML corpus completed with zero native-feed hits.
- The broader 22-site naming-only XML probe completed with zero native-feed hits; transport-limited sites remain inconclusive.
- A fresh direct Cloudflare Browser Rendering API test was attempted during this continuation. The configured account credential returned Cloudflare API error 2001 (rate limit exceeded) for the tested batch; one Kryptronix request did execute and exposed ordinary WordPress/WooCommerce plugins but no feed-plugin fingerprint. This does not establish feed absence.
- Public web research confirms the plugin-family rules above and reinforces that feed filenames/URLs are often store-specific, so plugin identification should precede filename guessing.

## Next productive execution order

1. Keep the known-ten exclusion locked.
2. Use the canonical 22-site manifest, not a hand-maintained list, as the runtime source of truth.
3. Run plugin extraction in independent shards: browser + homepage XHR, WP JSON/REST, WooCommerce v1/v2/v3 capability probes.
4. Normalize fingerprints and group sites by exact plugin family.
5. For each non-unknown group, run only that plugin's documented feed URL grammar.
6. For unknown sites, run bounded generic XML candidates plus URLs explicitly exposed in public HTML/robots/sitemaps/JS/network evidence.
7. Use Cloudflare Browser Rendering only when the account is authorized and rate limits permit; do not bypass challenges.
8. Validate every candidate at payload level and preserve transport state separately.
9. Update the plugin-group ledger before adding more candidate patterns; this prevents repeated work and uncontrolled URL explosion.

## Evidence references

- GitHub issue #1247: canonical WooCommerce native-feed recovery.
- Historical/runtime work: PR #1564 and its recorded 22-site V175 recovery receipts.
- Current native feed verification baseline: Only SDD remains the already-verified native feed.
