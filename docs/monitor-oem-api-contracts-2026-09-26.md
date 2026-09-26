# Monitor OEM API / Specification Contract Map — 2026-09-26

Scope: Acer, MSI, Samsung, AOC, Dell, ROG, ASUS, BenQ, Gigabyte, AORUS, LG.

## Qualification rule
A route is a **true catalog/spec API** only when it returns machine-readable product records or specification objects suitable for bulk extraction. A product-page HTML/PDF fallback is recorded separately and is not mislabeled as an API.

## Contracts

### ROG — qualified
Catalog:
https://api-rog.asus.com/recent-data/search-api/v1/ResultV1/in/Product/100/1/0/1?SearchKey=monitor&systemCode=rog

Spec:
https://api-rog.asus.com/recent-data/api/v4/Common/Spec?WebsiteCode=in&PartNo={PartNo}

Additional product endpoints:
- /recent-data/api/v5/Product/Spec?m1Id={m1Id}&WebsiteCode={WebsiteCode}
- /recent-data/api/v5/Product/ModelSpec?m1Id={m1Id}&WebsiteCode={WebsiteCode}
- /recent-data/api/v4/Product/Info?m1Id={m1Id}&WebsiteCode={WebsiteCode}
- /recent-data/api/v4/Product/Tabs?m1Id={m1Id}&WebsiteCode={WebsiteCode}

Status: QUALIFIED. Live API validation returned rich structured specs including panel size, panel type, resolution, gamut, brightness, HDR peak, contrast, response time, refresh rate, color depth, and more.

### Dell — qualified
Catalog:
https://www.dellstore.com/rest/V1/products?searchCriteria%5BpageSize%5D=100&searchCriteria%5BcurrentPage%5D=3

Status: QUALIFIED. Live Magento REST product records include url_key, product IDs, display characteristics, connectivity, panel type, refresh/resolution information, pricing and stock-related fields.

### Samsung — qualified
Catalog:
https://p1-smi-api-cdn.shop.samsung.com/tokocommercewebservices/v2/in/products/search?query=monitor%3Arelevance&pageSize=100&currentPage=0&fields=FULL

Public technical spec service:
https://searchapi.samsung.com/v6/front/b2c/product/spec/detail?siteCode={siteCode}&modelList={modelCode}&specAnnotationYN=N

Monitor finder:
https://searchapi.samsung.com/v6/front/b2c/product/finder/global?type=07010000&siteCode={siteCode}&start=1&num=12&sort=newest&onlyFilterInfoYN=N&keySummaryYN=Y

Status: QUALIFIED as a two-stage catalog + technical-spec service. Public source implementations use attrName/attrValue from the technical-spec response.

### ASUS mainline — qualified for product discovery + official tech-spec route
Catalog:
https://odinapi.asus.com/recent-data/apiv2/SearchResult?SystemCode=asus&WebsiteCode=in&SearchKey=monitor&SearchType=products&PageSize=100&Pages=1&LocalFlag=0&siteID=www&sitelang=

Product metadata route:
https://odinapi.asus.com/recent-data/apiv2/PDTablist?SystemCode=asus&WebsiteCode=in&ProductLevel1Code=displays-desktops&ProductLevel2Code=monitors&SeriesWebPath={series}&ProductWebPath={product}&ProductTabWebPath=&siteID=www&sitelang=

Tech spec page route:
https://www.asus.com/in/displays-desktops/monitors/{series}/{product}/techspec/

Supporting API family:
- /recent-data/apiv2/PDTab
- /recent-data/apiv2/PDSectionList
- /recent-data/apiv2/PDFiles
- /recent-data/apiv2/GetMeta
- /recent-data/apiv2/PDReview

Status: QUALIFIED for discovery and manufacturer-owned technical-spec acquisition. The current product page state explicitly exposes a Tech Specs tab and PDTechSpec store.

### Acer — qualified fallback; GraphQL contract identified
Endpoint:
https://store.acer.com/en-in/graphql

Platform: Magento GraphQL.

Current storefront schema requires either search or filter input for product queries. The V175 host profile already routes Acer India through the GraphQL specialist path.

Status: QUALIFIED FALLBACK. Exact monitor product/spec query schema still depends on current Acer GraphQL deployment; official rendered PDP remains the safe fallback rather than inventing a schema.

### LG — qualified official spec path; API contract identified
Current product page exposes:
https://www.lg.com/in/api/commerce/content/pdp_items

Frontend contract:
- locale
- sku
- product_name
- category

Response contract used by current frontend:
items.keyspec

Page store configuration also exposes:
- /api/graphql
- locale=en-IN

Status: QUALIFIED FALLBACK / API-CONTRACT-FOUND. The exact PDP-items request requires the current frontend request context/header behavior; direct unauthenticated replay returned an LG error page during validation. Do not bypass it. The rendered manufacturer PDP remains authoritative.

### BenQ — qualified official spec fallback
Official spec page:
https://www.benq.com/en-in/monitor/gaming/ex271/spec.html

Current page is a structured g6-product-spec-page with an extensive All Specifications dataset.

Discovered commerce API family:
https://www.benq.com/api/magento/g6/queryMixedProduct/BQP/in-buy

Status: QUALIFIED FALLBACK. The commerce API is not promoted to a technical-spec API until its request contract is fully reproducible.

### Gigabyte — API found; direct access blocked
Known backend family:
- /api/v1.0/Consumer/{countryCode}/Consumer/{productCategoryUrl}/{modelUrl}
- /api/v1.0/Consumer/{countryCode}/GetProductTabDataAsync/{apiUseTabKey}/{pid}
- /api/v1.0/OneData/{countryCode}/GetOneDataSpecAsync?sn={sn}&model={model}&sku={sku}

Public frontend proxy family:
https://www.gigabyte.com/iisApplicationNuxt/api/proxy/api/v1.0/...

Status: API FOUND / ACCESS BLOCKED. Current direct extraction attempts receive Akamai/403 from runner infrastructure. Use the official PDP /sp specification page or an allowed public frontend proxy route when it is actually exposed.

### AORUS — Gigabyte family
AORUS uses the same Gigabyte product platform family for monitor data.

Status: API FAMILY IDENTIFIED / ACCESS BLOCKED. Treat AORUS as a Gigabyte adapter variant, not a separate generic scraper.

### AOC — qualified official PDP extraction
Validated APIs:
- /api/products/screen-size-variants?locale={locale}&brand={brand}&productId={productId}&series={series}
- /api/products/price-data?sku={sku}&locale={locale}&brand={brand}

The first returns variant links; the second returns store/price/status data.

Status: QUALIFIED FALLBACK. No full technical-spec JSON API was positively identified. V175's dedicated AOC PDP parser is therefore the intended technical-spec path.

### MSI — qualified official specification/PDF fallback
Official specification pages:
https://www.msi.com/Monitor/{model}/Specification

Official datasheet family:
https://storage-asset.msi.com/datasheet/monitor/{region}/{file}.pdf

Status: QUALIFIED FALLBACK. MSI's Akamai-protected HTML frequently blocks automated runners; the official datasheet/spec page provides comprehensive manufacturer data.

## Canonical adapter strategy

1. ROG / Dell / Samsung / ASUS: structured catalog/API first.
2. LG / Acer / BenQ: structured manufacturer PDP/API where reproducible; otherwise official rendered page.
3. Gigabyte / AORUS: backend API known, but honor access controls and use exposed proxy/PDP fallback.
4. AOC / MSI: official PDP/PDF specialist extraction.
5. Normalize all routes into the existing V175 monitor schema and retain source URL + acquisition method + evidence fields.

No third-party spec source is used as the source of truth when a manufacturer-owned source exists.
