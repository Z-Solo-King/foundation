# ChatGPT Session Handoff — 2026-09-26

## Purpose

This file is the durable handoff for the next ChatGPT conversation. Resume from repository state and this document; do not assume the previous chat transcript is available.

## Repository / branch state

- Repository: `Z-Solo-King/foundation`
- Working branch: `probe/monitor-oem-api-20260926`
- Current branch HEAD: `3247bca0c4d003b20dbfe60b9186a426d1f9be0e`
- Latest commit: `test: add parallel Shopify Google feed discovery`
- This branch is exploratory. Do NOT merge exploratory work to `main` unless separately validated.
- Foundation canonical `main` head previously recorded: `f9eac33f3cae4eaff06b05262a0623dd0a69b87e`.
- Operations canonical `main` head previously recorded: `79f5e4e413f663fc2d8484acd090676fbe957625`.

## Primary extractor source

- User-provided universal extractor: `extract_universal_V175.py`
- Conversation file/library id: `file_0000000014d882088dc1c3c8a84fcd11`
- Library file id: `libfile_b8da263085a881918ba32fee16a68c82`
- Size: 1,514,139 bytes
- Lines: 33,411
- Use V175 as the pattern/source-of-truth for existing platform adapters and fallback strategies.

## Work completed immediately before this handoff: OEM/manufacturer monitor APIs

Target OEMs:
Acer, MSI, Samsung, AOC, Dell, ROG ASUS, ASUS, BenQ, Gigabyte, AORUS, LG.

### Confirmed / strong contracts

#### ROG ASUS
Product search:
GET
`https://api-rog.asus.com/recent-data/search-api/v1/ResultV1/{websiteCode}/Product/{pageSize}/{page}/{categoryId}/1?SearchKey={searchKey}&systemCode={systemCode}`

India:
- websiteCode=in
- systemCode=rog
- SearchKey=monitor
- pageSize=100
- categoryId=0
- page=1

Detailed spec:
GET
`https://api-rog.asus.com/recent-data/api/v4/Common/Spec?WebsiteCode=in&PartNo={PART_NO}`

Other exact ROG spec/info routes found:
- `/recent-data/api/v5/Product/Spec?m1Id={m1Id}&WebsiteCode={WebsiteCode}`
- `/recent-data/api/v5/Product/ModelSpec?m1Id={m1Id}&WebsiteCode={WebsiteCode}`
- `/recent-data/api/v4/Product/Info?m1Id={m1Id}&WebsiteCode={WebsiteCode}`
- `/recent-data/api/v4/Product/Tabs?m1Id={m1Id}&WebsiteCode={WebsiteCode}`

Live validation succeeded for ROG search and spec. Status: QUALIFIED.

#### ASUS mainline
Search:
GET
`https://odinapi.asus.com/recent-data/apiv2/SearchResult?SystemCode={systemCode}&WebsiteCode={websiteCode}&SearchKey=monitor&SearchType=products&SearchPDLine={searchPDLine}&SearchPDLine2={searchPDLine2}&PDLineFilter=&TopicFilter=&CateFilter=&PageSize=100&Pages=1&LocalFlag=0&siteID=www&sitelang=`

Response exposes ProductURL, ProductID, M1Id, PartNo, SalesModelName, Name, ModelSpec.

Status: product discovery QUALIFIED; mainline detailed-spec route still unresolved.

#### Samsung
Monitor finder:
GET
`https://searchapi.samsung.com/v6/front/b2c/product/finder/global?type=07010000&siteCode=in&start=1&num=100&sort=newest&onlyFilterInfoYN=N&keySummaryYN=Y`

Important category code:
- 07010000 = monitor

Full technical specification:
GET
`https://searchapi.samsung.com/v6/front/b2c/product/spec/detail?siteCode=in&modelList={MODEL_CODE}&specAnnotationYN=N`

Public code implementations confirm this exact endpoint and parse attrName/attrValue specification data.

Samsung India also has the OCC catalog/product API family already implemented in V175:
Base:
`https://p1-smi-api-cdn.shop.samsung.com/tokocommercewebservices/v2/in`

Catalog search:
GET `/products/search?query={PREFIX}:relevance&pageSize={N}&currentPage={N}&fields=DEFAULT`

Product batch:
GET `/products?productCodes={comma-separated-codes}&fields=FULL`

Status: Samsung moved from PARTIAL to API FOUND / strong candidate. Next live validation should exercise `product/spec/detail` using a current monitor model code.

#### Dell
GET
`https://www.dellstore.com/rest/V1/products?searchCriteria[pageSize]=100&searchCriteria[currentPage]=1`

Monitor product objects expose Magento custom attributes including:
- diagonal_size
- resolution_refresh_rate
- adaptive_sync
- response_time
- ports
- panel
- display_type
- features
- resolution
- refresh_rate
- aspect_ratio
- product_line
- dell_productid
- images
- price

Status: QUALIFIED.

#### LG
Coveo catalog route already implemented in V175:
- token: GET `https://www.lg.com/ncms/api/v1/coveo/token`
- search: POST `https://platform-eu.cloud.coveo.com/rest/search/v2?organizationId=lgcorporationproduction0fxcu0qx`
- payload includes q, numberOfResults, firstResult, locale=en-IN

Structured PDP content route found in frontend:
GET
`https://www.lg.com/in/api/commerce/content/pdp_items?locale={locale}&sku={sku}&product_name={product_name}&category={category}`

Current traced example:
- sku: `27GX790A-B.ATR.EAIL.IN.C`
- category: `monitors/ultragear-gaming-oled-monitors`
- response field consumed by frontend: `items.keyspec`

Status: API contract FOUND; direct API live execution should still be validated in the next pass.

#### Gigabyte / AORUS
First-party API family found in frontend source:
GET
`https://www.gigabyte.com/api/v1.0/Consumer/{countryCode}/Consumer/{productCategoryUrl}/{modelUrl}?type={type}`

GET
`https://www.gigabyte.com/api/v1.0/Consumer/{countryCode}/GetProductTabDataAsync/{apiUseTabKey}/{pid}`

GET
`https://www.gigabyte.com/api/v1.0/OneData/{countryCode}/GetOneDataSpecAsync?sn={sn}&model={model}&sku={sku}`

Also search/filter family:
- `/api/v1.0/Product/{countryCode}/MatchUrlSettingAndFilter/{category}/{productLineUrl}`
- `/api/v1.0/ProductFilter/{countryCode}/{productLineUrl}/ProductLineUrlToClassKey`
- `/api/v1.0/Search/{country}/GetSearchRecommend`

Direct GitHub-runner requests are affected by Akamai/403. Do not bypass security. Use an ordinary public frontend route/proxy or Browser Rendering if available.

AORUS appears to share the Gigabyte backend ecosystem.

Status: API FOUND, transport/access blocked on normal runner.

#### Acer
First-party GraphQL:
POST
`https://store.acer.com/en-in/graphql`

Schema/introspection previously exposed:
- products
- getCategoryFilters
- getSearchFilters
- hyvaProductAttribute
- xsearchProducts

V175 identifies Acer India as GraphQL-based and notes that Cloudflare/Akamai warming/access may be needed.

Status: promising, exact products query/input not yet fully resolved.

#### BenQ
Official structured specification page:
`https://www.benq.com/en-in/monitor/gaming/ex271/spec.html`

Internal API family found:
- `https://www.benq.com/api/magento/profile`
- `https://www.benq.com/api/magento/g6/queryMixedProduct/BQP/in-buy`

Complete request body/contract has NOT been validated.

Status: detailed spec extraction QUALIFIED via official spec page; internal API unresolved.

#### MSI
Official specification page:
`https://www.msi.com/Monitor/MAG-274UPF/Specification`

V175 PDF fallback:
GET
`https://storage-asset.msi.com/datasheet/monitor/global/{MODEL}.pdf`
Fallbacks:
- `https://storage-asset.msi.com/datasheet/monitor/en/{MODEL}.pdf`
- `https://storage-asset.msi.com/datasheet/monitor/global/{MODEL_WITH_UNDERSCORES}.pdf`

V175 parses PDF into fields such as DCI-P3, sRGB, brightness, peak brightness, HDR type, and frame sync.

Status: official spec/PDF fallback QUALIFIED; structured JSON API unresolved.

#### AOC
Variant API:
GET
`https://www.aoc.com/api/products/screen-size-variants?locale=en-in&brand=aoc&productId=27G4&series=G4`

Returns related screen-size product URLs.

Specification method:
GET official AOC PDP and use V175 `extract_monitor_specs_from_html` / `aoc_fetch_parse`.

Status: detailed spec extraction QUALIFIED; variant API is auxiliary, not full-spec API.

## Existing OEM validation workflows / commits

- `Monitor OEM Final Contract Validation`: run 36235439176, success; artifact 10903598393.
- `Monitor OEM Spec API Validation`: run 36235286327; artifact 10904215922.
- `Monitor OEM Source Trace`: run 36235172042; artifact 10903678123.
- Parallel remaining-OEM workflow:
  `.github/workflows/monitor-oem-remaining-parallel.yml`
  commit `c1b425e8e4f0b86115c7687734e442b58acb2969`.
  It probes Acer/Samsung/BenQ/LG/Gigabyte/AORUS/AOC/MSI in parallel.
- Do not claim a workflow succeeded unless its run/artifact has actually been inspected.

## CURRENT NEXT TASK: Shopify Google Shopping feed XML backup

The user now wants to research Shopify-based Indian retailers and find **Google feed XML backups**, because retailer API access may become Cloudflare-protected. Shopify JSON/GraphQL remains primary where already present, but Google feed XML is explicitly a backup.

Important distinction:
- Do NOT replace existing Shopify API extraction.
- Search for Google Shopping/feed XML as a resilient fallback.
- Use guessing + extraction + sitemap discovery + page/source inspection.
- Preserve stock information from existing API when available.
- Bitkart is confirmed as Shopify and is intentionally using search instead of Shopify API for normal extraction because of stock-info limitations; its `/products.json` is still useful as a backup discovery route.

### Shopify retailers in the provided master list

PC/computer retailers:
- Bitkart — Search — `https://bitkart.com/search?page=1&q=%2A`
  Existing alt: `https://bitkart.com/products.json`
- Elitehubs — GraphQL — `https://elitehubs.com/products.json`
- Genesis PC — `https://www.genesispc.in/products.json`
- Get Right PC — `https://getrightpc.com/products.json`
- Hardware Nest — `https://hardwarenest.in/products.json`
- mehtabrothers — `https://mehtabrothers.in/products.json`
- TLG Gaming — `https://tlggaming.com/llm_products.json`
- TPS Tech — `https://tpstech.in/products.json`
- vajawatcomputers — website previously marked down; alt `https://vajawatcomputers.com/products.json`
- Vishal Peripherals — `https://vishalperipherals.com/products.json`

Keyboard/peripherals:
- AceKBD — `https://acekbd.com/products.json`
- Amkette (EvoFox) — `https://www.amkette.com/products.json`
- Ant Esports — `https://antesports.com/products.json`
- Concept Kart — `https://conceptkart.com/products.json`
- Credkeys — `https://credkeys.com/products.json`
- CtrlShiftstore — `https://ctrlshiftstore.com/products.json`
- Curiosity Caps — `https://curiositycaps.in/products.json`
- CyberArt — `https://cybeart.in/products.json`
- fictioo — `https://fictioo.com/products.json`
- Genesis PC — `https://www.genesispc.in/products.json`
- Hardware Corpus — `https://hardwarecorpus.in/products.json`
- Keebsmod — `https://keebsmod.com/products.json`
- Keychron India — `https://www.keychron.in/products.json`
- Keyora — `https://keyora.store/products.json`
- Kreo — `https://kreo-tech.com/products.json`
- lethalblack — `https://lethalblack.com/products.json`
- Neomacro — `https://neomacro.in/products.json`
- NMPC — `https://www.nmpc.in/products.json`
- Portronics — `https://www.portronics.com/products.json`
- Redragon India — `https://www.redragon.in/products.json`
- Ryugear — `https://ryugear.in/products.json`
- Senpai Arts — `https://senpaiarts.com/products.json`
- thockshop — `https://thethockshop.com/products.json`
- TVS Electronics — `https://store.tvselectronics.in/products.json`
- URX — `https://urx.co.in/products.json`
- varmiloindia — `https://varmiloindia.com/products.json`
- vrkaa — `https://vrkaa.com/products.json`
- Waimers — `https://waimers.in/products.json`
- Zebronics — `https://zebronics.com/products.json`
- Zukabus — `https://zukabus.com/products.json`
- virtualracinghub — Shopify listed, no products.json alt supplied

Audio:
- AV Store — `https://avstore.in/products.json`
- Bajaao — `https://www.bajaao.com/products.json`
- boAt — `https://www.boat-lifestyle.com/products.json`
- Boult — `https://goboult.co.in/products.json`
- Headphone Zone — `https://headphonezone.in/products.json`
- Jamsticks — `https://www.jamsticks.com/products.json`
- Mivi — Shopify; current row has homepage link `https://www.mivi.in/`
- Noise — `https://www.gonoise.com/products.json`
- pTron — `https://ptron.in/products.json`
- The Audio Store — `https://www.theaudiostore.in/products.json`
- Theaudio.co — `https://theaudio.co/products.json`

### Already-known non-Shopify feeds in the same master list

Do not accidentally reclassify these:
- Computech stores — feed `https://computechstore.in/merchant-feed.xml`, sitemap `https://computechstore.in/sitemap.xml`
- DigiBuggy — sitemap `https://digibuggy.com/sitemap.xml`
- therhythmhouse — sitemap `https://www.therhythmhouse.co.in/sitemap_products.xml`
- altf4gear — sitemap `https://altf4gear.com/sitemap.xml`
- moddest — `https://www.moddest.in/google-shopping.xml`
- National PC — Google feed route `https://nationalpc.in/index.php?route=extension%2Fmodule%2Fgoogle_all_feed&feed_id=1`
- Vedant — `https://www.vedantcomputers.com/index.php?route=extension/feed/google_sitemap`
These are useful examples/patterns but are not Shopify targets.

## Shopify Google feed discovery strategy

For each Shopify domain, investigate in this order:

1. Store/product sitemap:
   - `/sitemap.xml`
   - `/sitemap_products_1.xml?from=...&to=...`
   - Shopify product sitemap variants
2. Google/feed naming guesses:
   - `/google-shopping.xml`
   - `/google_feed.xml`
   - `/google-feed.xml`
   - `/google_merchant.xml`
   - `/merchant-feed.xml`
   - `/product-feed.xml`
   - `/products-feed.xml`
   - `/feeds/google.xml`
   - `/feed/google.xml`
   - `/apps/google-shopping-feed`
   - app-specific feed URLs discovered from source
3. robots.txt / sitemap index:
   - `/robots.txt`
   - parse Sitemap lines and feed references
4. HTML/source/script extraction:
   - search for `google_product_category`, `google_merchant`, `merchant`, `feed`, `content_api`, `gmc`, `shopping`, `xml`, `atom`
   - inspect app/proxy URLs
5. Shopify app/feed providers:
   - identify installed public feed app from script/source URLs where possible
   - recover its actual public feed endpoint
6. Validate candidate feed:
   - HTTP status
   - Content-Type
   - XML parse
   - item/product count
   - presence of product link/title/id/price/availability
   - Indian INR currency where applicable
   - reject generic sitemap if it contains only URL nodes and no product feed fields
7. Cross-check feed coverage against `/products.json` and/or existing GraphQL catalog.
8. Record exact feed URL, HTTP method, discovery method, validation result, and count.

## Desired output schema for Shopify feed research

Per domain, record:
- brand
- domain
- platform=shopify
- feed_url
- method=GET/POST
- feed_type=google_merchant/rss/atom/xml/sitemap/app_feed/unknown
- discovery=guess/robots/source/script/app/proxy/sitemap
- status_code
- content_type
- xml_valid
- product_count
- has_link
- has_title
- has_price
- has_availability
- currency
- stock_quality
- fallback_rank
- notes
- checked_at

## Implementation / safety rules

- Use public endpoints and normal application behavior only.
- Do not bypass Cloudflare, Akamai, bot challenges, authentication, or access controls.
- When direct runner access is blocked, record the blocker and test an ordinary public frontend-accessible route/Browser Rendering where available.
- Prefer first-party feed endpoints over third-party mirrors.
- Do not call a guessed URL “confirmed” until it returns a valid feed.
- Keep exploratory work on `probe/monitor-oem-api-20260926` until validated.
- Parallelize Shopify discovery with bounded concurrency.
- Use GitHub Actions artifacts as machine-readable evidence.
- Do not modify production/main as part of exploratory feed discovery.

## Immediate next actions in the next chat

A. Finish/inspect the already-created Shopify parallel Google-feed workflow in `.github/workflows/` and its latest run/artifact. The current branch HEAD commit message is `test: add parallel Shopify Google feed discovery`.

B. Build/extend a bounded parallel Shopify feed probe for the full Shopify list above.

C. Check every Shopify domain for:
`robots.txt`, `sitemap.xml`, Shopify product sitemaps, common Google Merchant feed guesses, and feed/app references in HTML/scripts.

D. Prioritize Bitkart, Elitehubs, Genesis PC, Get Right PC, Hardware Nest, Mehtabrothers, TLG Gaming, TPS Tech, Vishal Peripherals, AceKBD, Concept Kart, Keychron India, Kreo, Redragon India, Headphone Zone, boAt, Noise, Bajaao, Zebronics.

E. Store exact validated feed routes in an evidence artifact and then update V175 only after contracts are stable.

## Important existing branch context

Recent commit sequence on this branch:
- `3841bd9ea8e72e911f9531851d46a7d7a93ad4b7` — trace exact OEM monitor API request contracts
- `79764cc6cd279d6a4941a7b6c16800cbafdad631` — final monitor product/spec API contract validation
- `c1b425e8e4f0b86115c7687734e442b58acb2969` — parallel remaining OEM monitor validation
- `63e5652a5c008e5f830e9277e216422210e28f42` — record monitor OEM API/fallback contracts
- `3247bca0c4d003b20dbfe60b9186a426d1f9be0e` — add parallel Shopify Google feed discovery

Resume from the latest commit and preserve the exploratory/non-production boundary.
