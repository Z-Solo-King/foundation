"""WooCommerce V175 discovery and validation primitives."""
from __future__ import annotations

try:
    from tools.woocommerce_v175_contracts import *
except ModuleNotFoundError:
    from woocommerce_v175_contracts import *

def bare_host(url: str) -> str:
    h = (urlsplit(url).hostname or "").lower()
    return h[4:] if h.startswith("www.") else h


def same_host(a: str, b: str) -> bool:
    return bare_host(a) == bare_host(b)


def is_challenge(status: int, body: str) -> bool:
    s = str(body or "")[:15000].lower()
    markers = (
        "just a moment", "cf-chl-", "cf-browser-verification", "cf-mitigated",
        "challenge-platform", "cf-turnstile", "cdn-cgi/challenge",
        "verify you are human", "attention required", "checking your browser",
        "access denied", "request blocked", "security rejection", "captcha",
        "turnstile",
    )
    if status in (403, 429, 430, 503, 520, 521, 522, 523, 524):
        return any(m in s for m in markers) or not s
    if status == 200 and any(m in s for m in markers):
        if "application/ld+json" in s and '"@type":"product"' in s:
            return False
        return True
    return False


def parse_plugin_slugs(text: str) -> List[str]:
    slugs = set(re.findall(r"/wp-content/plugins/([^/?#\"' <]+)/", text or "", re.I))
    return sorted(slugs)[:80]


def _normalize_namespace(value: str) -> str:
    # WordPress REST discovery may JSON-escape slashes as \\/.
    return str(value or "").replace(r"\/", "/").strip()


def parse_namespaces(text: str) -> List[str]:
    out = set()
    for m in re.finditer(r'"namespaces"\s*:\s*\[(.*?)\]', text or "", re.S):
        for item in re.findall(r'"([^"]+)"', m.group(1)):
            n = _normalize_namespace(item)
            if n:
                out.add(n)
    for m in re.findall(r'"([A-Za-z0-9_.-]+(?:\\/|/)[A-Za-z0-9_.-]+)"', text or ""):
        n = _normalize_namespace(m)
        if any(k in n.lower() for k in ("feed", "wpfm", "woo", "google", "merchant", "ctx")):
            out.add(n)
    return sorted(out)


def find_plugin_hits(blobs: Iterable[str], plugin_slugs: Iterable[str], namespaces: Iterable[str]) -> Dict[str, List[str]]:
    """Return family hits using family-exclusive fingerprints where possible.

    Generic page copy such as "Google Merchant Center" is not sufficient to
    classify a Google-for-WooCommerce integration. Strong fingerprints must be
    present in a plugin asset slug, REST namespace, resource URL, or explicit
    family-specific endpoint signature.
    """
    all_text = "\n".join(str(x or "") for x in blobs).lower()
    evidence = set(str(x).lower() for x in plugin_slugs)
    evidence.update(str(x).lower() for x in namespaces)
    hits: Dict[str, List[str]] = {}

    exclusive = {
        "woocommerce_google_product_feed": (
            "woocommerce_gpf", "woocommerce-gpf", "woocommerce-google-product-feed",
            "google_product_feed", "google-product-feed", "lw_woocommerce_gpf",
        ),
        "ctx_feed_webappick": (
            "ctx feed", "ctx-feed", "webappick", "woo_feed", "woo-feed",
            "webappick-product-feed-for-woocommerce",
        ),
        "adtribes_product_feed_pro": (
            "adtribes", "woo-product-feed-pro", "product-feed-pro",
            "woo-product-feed-pro-for-woocommerce",
        ),
        "wpfm_product_feed_manager": (
            "wppfm", "wppfm-feeds", "wpfm/v1",
            "product-feed-manager-for-woocommerce",
        ),
        "webtoffee_product_feed": (
            "webtoffee", "webtoffee_product_feed", "webtoffee-product-feed",
            "webtoffee-product-feed-for-woocommerce",
        ),
        "codesolz_merchant_feed_booster": (
            "codesolz", "codesolz-feeds", "merchant-feed-booster",
        ),
        "feedcraft": ("feedcraft", "feedcraft-product-feed", "thebasics-product-feed"),
        "google_for_woocommerce": (
            "google-listings-and-ads", "wc/gla", "google_merchant_center_plugin",
        ),
    }

    for family, needles in PLUGIN_RULES:
        family_hits = []
        strong = exclusive.get(family, needles)

        for e in evidence:
            for n in strong:
                if n in e:
                    family_hits.append(e)
                    break

        for n in strong:
            if n in all_text:
                family_hits.append(n)

        if family == "google_for_woocommerce":
            family_hits = [
                x for x in family_hits
                if x in {"google-listings-and-ads", "wc/gla", "google_merchant_center_plugin"}
                or "google-listings-and-ads" in x
                or "wc/gla" in x
            ]

        if family_hits:
            hits[family] = sorted(set(family_hits))[:20]
    return hits

def plugin_family_confidence(hits: Dict[str, List[str]], plugin_slugs: Iterable[str], namespaces: Iterable[str]) -> str:
    """Prefer concrete plugin asset evidence over generic page text."""
    if not hits:
        return "low"
    slugs = {str(x).lower() for x in plugin_slugs}
    ns = {str(x).lower() for x in namespaces}
    strong = {
        str(needle).lower()
        for family, needles in PLUGIN_RULES
        if family in hits
        for needle in needles
    }
    if any(any(n in s for n in strong) for s in slugs):
        return "high"
    if any(any(n in x for n in strong) for x in ns):
        return "medium"
    return "low"


def query_feed_candidates(text: str, root: str) -> List[str]:
    """Recover public feed URLs expressed as query parameters even when the slug is random."""
    out = set()
    for m in re.finditer(r"(?:[?&])(woo_feed|woocommerce_gpf)=([^&#\"' <>]+)", text or "", re.I):
        key, value = m.group(1), m.group(2)
        if not value:
            continue
        prefix = "/?"
        if key.lower() == "woo_feed":
            out.add(urljoin(root + "/", prefix + f"woo_feed={value}&wt=xml"))
            out.add(urljoin(root + "/", prefix + f"woo_feed={value}"))
        else:
            out.add(urljoin(root + "/", prefix + f"woocommerce_gpf={value}"))
            if value.lower() == "google":
                for start in (0, 100):
                    out.add(urljoin(root + "/", prefix + f"woocommerce_gpf=google&gpf_start={start}&gpf_limit=100"))
    for raw in re.findall(r"https?://[^\s\"'<>]+", text or "", re.I):
        u = raw.rstrip("),.;")
        if same_host(u, root) and PASSIVE_FEED_HINT_RE.search(u):
            out.add(u)
    return sorted(out)[:120]


def discover_urls_from_xml_or_text(text: str, root: str) -> List[str]:
    urls = set(explicit_xml_candidates(text, root))
    urls.update(query_feed_candidates(text, root))
    for raw in re.findall(r"(?:href|src|loc)=['\"]([^'\"]+)['\"]", text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and PASSIVE_FEED_HINT_RE.search(u):
            urls.add(u)
    return sorted(urls)[:200]


def passive_sitemap_candidates(text: str, root: str) -> List[str]:
    out = set(discover_urls_from_xml_or_text(text, root))
    for u in re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text or "", re.I):
        try:
            full = urljoin(root + "/", u)
        except Exception:
            continue
        if same_host(full, root) and PASSIVE_FEED_HINT_RE.search(full):
            out.add(full)
    return sorted(out)[:200]


def explicit_xml_candidates(text: str, root: str) -> List[str]:
    out = set()
    for raw in re.findall(r'https?://[^\s"\'<>]+', text or "", re.I):
        u = raw.rstrip("),.;")
        if not same_host(u, root):
            continue
        if re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I) or PASSIVE_FEED_HINT_RE.search(u):
            out.add(u)
    for raw in re.findall(r'''(?:href|src|loc)=["']([^"']+)["']''', text or "", re.I):
        try:
            u = urljoin(root + "/", raw)
        except Exception:
            continue
        if same_host(u, root) and (re.search(r"\.xml(?:\.gz)?(?:$|[?#])", u, re.I) or PASSIVE_FEED_HINT_RE.search(u)):
            out.add(u)
    return sorted(out)[:160]


def filter_explicit_feed_candidates(urls: Iterable[str]) -> List[str]:
    """Keep actual feed-like URLs, excluding sitemap/robots discovery documents."""
    out = set()
    for raw in urls:
        try:
            u = str(raw)
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if path.endswith("robots.txt") or "sitemap" in path:
            continue
        out.add(u)
    return sorted(out)[:160]


PLUGIN_FEED_DIRECTORIES = [
    "/wp-content/uploads/woo-feed/google/xml/",
    "/wp-content/uploads/woo-feed/google/",
    "/wp-content/uploads/woo-product-feed-pro/xml/",
    "/wp-content/uploads/wppfm-feeds/",
    "/wp-content/uploads/webtoffee_product_feed/",
    "/wp-content/uploads/codesolz-feeds/",
    "/feeds/",
    "/feed/",
]


def public_directory_feed_candidates(text: str, root: str, directory: str) -> List[str]:
    """Discover generated XML files from a public directory index; never invent filenames."""
    out = set()
    base = urljoin(root + "/", directory.lstrip("/"))
    for raw in re.findall(r'''(?:href|data-href)=["']([^"']+)["']''', text or "", re.I):
        if raw in ("../", "./", "#"):
            continue
        try:
            u = urljoin(base, raw)
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if not same_host(u, root):
            continue
        if not (path.endswith(".xml") or path.endswith(".xml.gz")):
            continue
        # Known plugin output directories may use arbitrary/generated filenames.
        out.add(u)
    for raw in re.findall(r'https?://[^\s"\'<>]+', text or "", re.I):
        try:
            u = raw.rstrip("),.;")
            path = (urlsplit(u).path or "").lower()
        except Exception:
            continue
        if same_host(u, root) and (path.endswith(".xml") or path.endswith(".xml.gz")):
            out.add(u)
    return sorted(out)[:120]


def native_verification_admissible(
    challenge_encountered: bool,
    clean_browser_success: bool,
    native_feed_verified: bool,
) -> bool:
    """Allow a standalone feed only when its own current payload is valid and public."""
    return bool(native_feed_verified or (clean_browser_success and not challenge_encountered))


def native_google_valid(body: bytes, content_type: str) -> Tuple[bool, int, str]:
    if not body:
        return False, 0, ""
    raw = body
    try:
        if raw[:2] == b"\x1f\x8b" or "gzip" in (content_type or "").lower():
            raw = gzip.decompress(raw)
    except Exception:
        return False, 0, ""
    text = raw.decode("utf-8", "ignore")
    low = text.lower()
    if not re.search(r"https?://base\.google\.com/ns/1\.0", low):
        return False, 0, ""
    if not re.search(r"<rss\b|<feed\b", low) or not re.search(r"<item\b|<entry\b", low):
        return False, 0, ""
    if re.search(r"just a moment|cf-chl-|turnstile|captcha|access denied|attention required|checking your browser", low):
        return False, 0, ""
    ids = re.search(r"<g:id\b[^>]*>(.*?)</g:id>", text, re.S | re.I)
    titles = re.search(r"<g:title\b[^>]*>(.*?)</g:title>", text, re.S | re.I)
    links = re.search(r"<g:link\b[^>]*>(.*?)</g:link>", text, re.S | re.I)
    prices = re.search(r"<g:price\b[^>]*>(.*?)</g:price>", text, re.S | re.I)
    if not all((ids, titles, links, prices)):
        return False, 0, ""
    count = len(re.findall(r"<(?:item|entry)\b", text, re.I))
    return True, count, hashlib.sha256(raw).hexdigest()
