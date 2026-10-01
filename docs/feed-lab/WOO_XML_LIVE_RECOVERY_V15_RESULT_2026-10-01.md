# WooCommerce Native Google Merchant XML Recovery — V15

Run: GitHub Actions 36829126387  
PR: #1692  
Corpus: exact 30-site learning corpus (10 calibration + 20 unknown; AULA included; Only SSD excluded)

## Result
0/30 current public native Google Merchant XML feed URLs verified.

Acceptance gate: current HTTP 200; same-host final URL; XML/RSS/Atom payload; not sitemap; Google Merchant namespace `base.google.com/ns/1.0`; at least one item/entry containing `g:id`, `g:title`, `g:link`, and `g:price`.

## Classification
| Site | Family | Result |
|---|---|---|
| PC Studio | Woo Product Feed | transport-limited |
| Quickin Computers | CTX Feed | transport-limited |
| Avikaretails | AdTribes | transport-limited |
| IT Gadgets Online | WPFM | reachable, no native feed |
| Geekbees | Google for WooCommerce | reachable, no feed URL |
| Ninja Dog | Google for WooCommerce | reachable, no feed URL |
| Network IT Store | Google for WooCommerce | reachable, no feed URL |
| My Nexus Infosys | Google for WooCommerce | reachable, no feed URL |
| Solanki Enterprises | Google for WooCommerce | reachable, no feed URL |
| AULA India | Google for WooCommerce | transport-limited |
| Aarna Computers | Unknown | transport-limited |
| Ads Store | Unknown | transport-limited |
| EZPZ Solutions | Unknown | reachable, no native feed |
| GamesNComps | Unknown | reachable, no native feed |
| hotshiftpc | Unknown | reachable, no native feed |
| ithunt | Unknown | transport-limited |
| KC Computers | Unknown | transport-limited |
| KRG KART | Unknown | transport-limited |
| PC Kumar Infotech | Unknown | transport-limited |
| PCHubShop | Unknown | transport-limited |
| SCL Gaming | Unknown | transport-limited |
| Variety Infotech | Google for WooCommerce | reachable, no feed URL |
| Viper PC | Unknown | reachable, no native feed |
| Cosmic Byte | Unknown | transport-limited |
| Meckeys | Unknown | reachable, no native feed |
| StacksKB | Unknown | reachable, no native feed |
| Theproaudio | Unknown | transport-limited |
| Prime ABGB | Woo Product Feed | reachable, tested paths non-Merchant XML |
| Kryptronix Gaming | WebToffee | transport-limited |
| NCL Computer | WebToffee | reachable, tested paths non-Merchant XML |

## Blockers
1. Exact filename/path guessing is not exhaustive. Feed plugins can use administrator-selected feed names, so fixed filenames cannot prove absence.
2. Google for WooCommerce has no traditional public feed URL: it syncs through Google's Content API for Shopping. A traditional feed URL requires a separate feed extension. citeturn915123search0
3. Feed-producing extensions expose their generated feed URL from their plugin/admin configuration. Product Feed Manager stores generated feeds under `/wp-content/uploads/wppfm-feeds/`, but the actual filename is configuration-dependent. citeturn915123search1turn915123search3
4. 15/30 targets were transport-limited from the GitHub runner (HTTP 403 and/or timeouts); this is an access limitation, not evidence that their XML does not exist.
5. Browser Rendering also encountered target Cloudflare protection, so no clearance/captcha bypass was used.

## What V15 fixed
- Correct 30-site corpus.
- Current live HTTP validation instead of archive-only inference.
- Same-host redirect validation.
- Strict Merchant namespace + core-field acceptance.
- Explicit separation of transport-limited from reachable/no-feed results.
- No Store API, product extraction, authentication, CAPTCHA bypass, clearance replay, proxy rotation, or random token enumeration.

The work therefore reaches an evidence-grade state: no current public native Merchant XML URL is verified from this corpus, and the remaining uncertainty is specifically target-side access control or non-public/configured feed URL discovery, not the XML validator.
