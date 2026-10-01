# WooCommerce Feed Recovery V8 — iCopyDoc family identification — 2026-10-01

V7 produced one family-specific signal on StacksKB: the current public endpoint
`/wp-content/uploads/feed-xml-0.xml` returned HTTP 200 with `application/xml`,
but the payload was empty.

Independent family research matched this exact path to the iCopyDoc WooCommerce
Google Merchant XML feed grammar. Therefore:

- family candidate: iCopyDoc;
- target: StacksKB;
- evidence strength: family-level URL-grammar corroboration;
- plugin identity: not proven;
- native Merchant XML: not verified.

V8 promotes the case only into a targeted family-recovery queue. It must not be
treated as final plugin identity and must not trigger arbitrary token/index
enumeration.
