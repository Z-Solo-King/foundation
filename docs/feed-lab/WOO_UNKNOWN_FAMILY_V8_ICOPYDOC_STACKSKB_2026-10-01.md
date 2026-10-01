# WooCommerce Feed Recovery V8 — iCopyDoc family evidence — 2026-10-01

## Target

StacksKB.

## V7 evidence

The V7 live run returned:

- current HTTP 200 from https://stackskb.com/wp-content/uploads/feed-xml-0.xml
- content type: application/xml
- response was not a challenge or access-denied page
- strict Merchant validator did not accept it because the payload was empty
- iCopyDoc expansion candidates returned HTTP 404
- no native Google Merchant XML URL was verified

## Independent family corroboration

iCopyDoc's published WooCommerce Google Merchant Center instructions explicitly reference the public feed path /wp-content/uploads/feed-xml-0.xml and discuss cases where that exact path is used as the feed URL. This independently supports the path as an iCopyDoc-family grammar.

This evidence supports:

- family candidate: iCopyDoc
- target: StacksKB
- family URL grammar: /wp-content/uploads/feed-xml-0.xml
- current transport state: public HTTP 200
- semantic feed state: empty / not a native Merchant feed

This does NOT prove that the iCopyDoc plugin is currently installed on StacksKB. Plugin identity requires corroborating current public fingerprint evidence.

## V8 decision

Promote StacksKB to the iCopyDoc family-candidate queue for V9 targeted grammar expansion, but do not promote it to verified plugin identity or verified native Merchant feed.

V9 should use only additional iCopyDoc-supported public grammar already evidenced by the family, plus deterministic current references. It must not enumerate random tokens or restart the broad cross-family matrix.

Source:
- iCopyDoc published WooCommerce Google Merchant Center feed documentation: https://icopydoc.ru/kak-sozdat-woocommerce-xml-instruktsiya/
