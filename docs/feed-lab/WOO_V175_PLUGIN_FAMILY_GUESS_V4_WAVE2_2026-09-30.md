# WooCommerce Plugin-Family XML Guess V4 — Wave 2

This is the actual guessing phase after the 30-site plugin extraction/grouping/research stage. No site extraction, plugin discovery, Store API extraction, sitemap discovery, robots discovery, or browser discovery is run here.

Wave 2 expands only the URL hypothesis grammar. Research-backed additions include CTX examples such as `listings07.xml`, `google_shopping_ctx_1.xml`, `google_shopping_ctx_1-3.xml`, `merchantcenter2.xml`, and `feed.xml`; WPFM examples such as `Google-Products-New.xml`; WebToffee filename forms such as `wt_fb_Feed.xml`; RexFeed's public `feed-<id>.xml` pattern; klpsoft's static `klp-feeds-xml` directory; and iCopyDoc's `feed-xml-0.xml` example.

Sources:
- WooCommerce GPF partial-feed URL grammar: citeturn497274search1turn497274search11
- CTX public URL/file examples: citeturn216332search1turn216332search7
- WPFM output directory and public feed examples: citeturn497274search10turn237758search2
- WebToffee file naming/cache example: citeturn237758search0turn237758search1
- CodeSolz fixed output path: citeturn497274search6
- FeedCraft public XML endpoint: citeturn497274search8
- RexFeed output directory/examples: citeturn216332search2turn216332search3turn216332search6
- klpsoft static directory: citeturn497274search0
- iCopyDoc example: citeturn428963search2

Acceptance remains strict: a current same-host response must contain the Google Merchant namespace and `g:id`, `g:title`, `g:link`, and `g:price` in one item/entry. A 403, 404, challenge page, timeout, sitemap, RSS, or unrelated XML is not a positive hit.
