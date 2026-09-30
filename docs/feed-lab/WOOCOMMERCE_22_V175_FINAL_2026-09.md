# WooCommerce 22-site V175 complete final evidence

Final V175 pipeline: GitHub Actions run 36668783363
Targeted WPFM proof: GitHub Actions run 36668801148

## Extraction methods used

- Playwright browser rendering
- Homepage XHR/fetch response URL capture
- WordPress WP-JSON root discovery (/wp-json/ and ?rest_route=/)
- WordPress REST wp/v2 discovery
- General REST/OPTIONS
- WooCommerce REST v1/v2/v3 root + products endpoint probes
- Public plugin asset fingerprinting
- Public plugin readme metadata

The v1/v2/v3 WooCommerce product requests are endpoint-presence probes. Response bodies are discarded and not persisted by this plugin-identification lane.

## Coverage

- 22/22 sites extracted successfully.
- 33/33 jobs in the complete V175 pipeline succeeded.
- New feed-plugin family established: 1.
- Native Google Merchant XML feeds verified in this 22-site lane: 0.

## Plugin grouping

- unknown_woocommerce: 21 — AULA India, Aarna Computers, Ads Store, Cosmic Byte, EZPZ Solutions, KC Computers, KRG KART, Kryptronix Gaming, Meckeys, Moskeys, NCL Computer, PC Kumar Infotech, PCHubShop, Prime ABGB, SCL Gaming, StacksKB, Theproaudio, Variety Infotech, Viper PC, hotshiftpc, ithunt
- wpfm_product_feed_manager: 1 — itgadgetsonline

## Important identified site

- itgadgetsonline -> wpfm_product_feed_manager.
- Evidence: public WP-JSON namespace wpfm/v1.
- WooCommerce REST product endpoint probes v1/v2/v3 returned 401 for product GETs while the version roots/options surfaces were reachable.
- WPFM XML hunt tested 175 candidates with 0 transport-limit events and 0 validated native Google Merchant XML feeds.

## Native XML result

No new native Google Merchant XML feed was verified across these 22 sites.

## Interpretation

The requested transport expansion was implemented and exercised across the full 22-site set. The extractor now distinguishes browser reachability, REST surface, XHR evidence, plugin assets, and feed-family signals rather than treating a blocked homepage as the only signal.

Only itgadgetsonline acquired a new feed-family assignment. The other 21 remain unknown because the permitted public evidence did not establish a specific feed plugin family.

The WPFM result remains filename-limited. Product Feed Manager documentation states that generated feeds are stored under /wp-content/uploads/wppfm-feeds/ and that the feed list shows the generated URL. Public examples show merchant/site-specific filenames, so filename recovery is not guaranteed without additional public filename evidence.

## External verification

WordPress REST discovery documents that the API root exposes namespaces and that plugin-registered REST namespaces can be used for extension discovery.

WooCommerce's code reference documents product controllers under wc/v1, wc/v2 and wc/v3.

WooCommerce Product Feed Manager documentation states that generated feeds are stored in /wp-content/uploads/wppfm-feeds/ and that the feed list exposes the feed URL.
