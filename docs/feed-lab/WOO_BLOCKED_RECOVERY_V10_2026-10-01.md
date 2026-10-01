# WooCommerce Persistent Blocked Recovery V10 — 2026-10-01

This stage follows V7 and the documented-family V8/V9 work. It addresses only the persistent transport-blocked targets from V7 run 36820461029.

Ten targets are included because V7 classified them as transport-limited. Each target is probed sequentially through the ten already-researched family representative URLs. There is a 1.5-second spacing between probes and one slow retry for 403/429/timeout. No family expansion is performed unless a current public response changes the evidence state.

A 403/429/timeout remains transport-unverified. Native certification still requires current same-host HTTP 200 XML/RSS/Atom-like output with the Google Merchant namespace and g:id/g:title/g:link/g:price in the same item/entry.

No CAPTCHA solving, Cloudflare challenge bypass, clearance-cookie replay, authentication bypass, proxy rotation/evasion or random token enumeration is used.
