"""Deterministic text/identifier normalization for product records.

Ported from the legacy V18 mapper's general-cleaning layer. Pure text
processing only: no network I/O, no anti-bot/acquisition logic. Brand and
category alias tables are declarative domain knowledge (India PC-component
and electronics retail categories).
"""
from __future__ import annotations

import html
import re
import unicodedata
from functools import lru_cache
from typing import Any, Dict

BRAND_ALIASES: Dict[str, str] = {
    "asus": "asus",
    "asustek": "asus",
    "asus computer": "asus",
    "msi": "msi",
    "micro star international": "msi",
    "gigabyte": "gigabyte",
    "gigabyte technology": "gigabyte",
    "zotac": "zotac",
    "corsair": "corsair",
    "kingston": "kingston",
    "kingston technology": "kingston",
    "samsung": "samsung",
    "western digital": "western digital",
    "wd": "western digital",
    "sandisk": "sandisk",
    "seagate": "seagate",
    "logitech": "logitech",
    "acer": "acer",
    "lenovo": "lenovo",
    "hp": "hp",
    "hewlett-packard": "hp",
    "hewlett packard": "hp",
    "dell": "dell",
    "dell technologies": "dell",
    "filco": "filco",
    "ducky": "ducky",
    "8bitdo": "8bitdo",
    "a4tech": "a4tech",
    "bloody": "bloody",
    "attack shark": "attack shark",
    "varmilo": "varmilo",
    "drunkdeer": "drunkdeer",
    "epomaker": "epomaker",
    "benq": "benq",
    "viewsonic": "viewsonic",
    "razer": "razer",
    "nvidia": "nvidia",
    "amd": "amd",
    "intel": "intel",
    "cooler master": "cooler master",
    "antec": "antec",
    "ek": "ekwb",
    "ekwb": "ekwb",
    "teamgroup": "teamgroup",
    "g skill": "g skill",
    "g.skill": "g skill",
    "crucial": "crucial",
    "lexar": "lexar",
    "thermaltake": "thermaltake",
    "deepcool": "deepcool",
    "nzxt": "nzxt",
    "fractal design": "fractal design",
    "lian li": "lian li",
    "arctic": "arctic",
    "noctua": "noctua",
    "alienware": "alienware",
    "apple": "apple",
    "adam audio": "adam audio",
    "sennheiser": "sennheiser",
    "beyerdynamic": "beyerdynamic",
    "audio technica": "audio-technica",
    "audio-technica": "audio-technica",
    "audeze": "audeze",
    "moondrop": "moondrop",
    "fiio": "fiio",
}
KNOWN_CANONICAL_BRANDS = frozenset(BRAND_ALIASES.values())

CATEGORY_ALIASES: Dict[str, str] = {
    "graphics card": "gpu",
    "graphic card": "gpu",
    "video card": "gpu",
    "gpu": "gpu",
    "processor": "cpu",
    "cpu": "cpu",
    "central processing unit": "cpu",
    "motherboard": "motherboard",
    "mainboard": "motherboard",
    "memory": "ram",
    "ram": "ram",
    "ddr memory": "ram",
    "solid state drive": "storage",
    "ssd": "storage",
    "nvme": "storage",
    "hard disk": "storage",
    "hdd": "storage",
    "storage": "storage",
    "power supply": "psu",
    "power supply unit": "psu",
    "psu": "psu",
    "monitor": "monitor",
    "display": "monitor",
    "mouse": "mouse",
    "keyboard": "keyboard",
    "headset": "headphones",
    "headphones": "headphones",
    "headphone": "headphones",
    "earbuds": "headphones",
    "true wireless earbuds": "headphones",
    "wired earbuds": "headphones",
    "studio headphonespro": "headphones",
    "open ear": "headphones",
    "open-ear": "headphones",
    "studio headphones": "headphones",
    "iem": "iem",
    "iems": "iem",
    "in ear monitor": "iem",
    "in-ear monitor": "iem",
    "in ear monitors": "iem",
    "earphone": "iem",
    "earphones": "iem",
    "wired earphones": "iem",
    "speaker": "speaker",
    "speakers": "speaker",
    "subwoofer": "speaker",
    "subwoofers": "speaker",
    "home subwoofer": "speaker",
    "powered subwoofer": "speaker",
    "monitor speakers": "speaker",
    "studio monitor speakers": "speaker",
    "studio monitor speaker": "speaker",
    "controller": "controller",
    "controllers": "controller",
    "game pedal": "controller",
    "clutch pedal": "controller",
    "racing pedal": "controller",
    "keycap": "keycap",
    "keycaps": "keycap",
    "switch": "switch",
    "switches": "switch",
    "game controller": "controller",
    "game controllers": "controller",
    "gaming controller": "controller",
    "gaming controllers": "controller",
    "case": "case",
    "cabinet": "case",
    "chassis": "case",
    "cooler": "cooler",
    "gaming laptop": "laptop",
    "notebook pc": "laptop",
    "laptop": "laptop",
    "laptops": "laptop",
    "notebook": "laptop",
    "notebooks": "laptop",
    "ultrabook": "laptop",
    "netbook": "laptop",
    "thin and light laptop": "laptop",
    "2 in 1": "laptop",
    "2-in-1": "laptop",
    "hybrid laptop": "laptop",
    "hybrid": "laptop",
    "desktop": "desktop",
    "desktop pc": "desktop",
    "all in one": "desktop",
    "all-in-one": "desktop",
    "imac": "desktop",
    "mac mini": "desktop",
    "cpu cooler": "cooler",
    "aio": "cooler",
}

_DASH_TRANSLATION = str.maketrans({
    "\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-",
})


@lru_cache(maxsize=32768)
def _clean_text_cached(text: str) -> str:
    """Cached core text cleaning for already-string inputs."""
    text = unicodedata.normalize("NFKC", html.unescape(text))
    text = text.translate(_DASH_TRANSLATION)
    return re.sub(r"\s+", " ", text).strip()


def clean_text(value: Any) -> str:
    """Normalize text deterministically; cached for repeated scalar values."""
    if value is None:
        return ""
    return _clean_text_cached(str(value))


@lru_cache(maxsize=32768)
def _normalize_brand_cached(raw: str) -> str:
    raw = re.sub(r"\s+", " ", raw).strip(" ._-\t")
    return BRAND_ALIASES.get(raw, raw)


def normalize_brand(value: Any) -> str:
    """Normalize a manufacturer/vendor name without losing semantic aliases."""
    return _normalize_brand_cached(clean_text(value).casefold())


@lru_cache(maxsize=32768)
def _normalize_category_cached(raw: str) -> str:
    if not raw:
        return ""
    raw = re.sub(r"[_\-/]+", " ", raw)
    raw = re.sub(r"\s+", " ", raw).strip(" . ")
    exact = CATEGORY_ALIASES.get(raw)
    if exact:
        return exact
    # Accessories must not inherit the parent product family.
    if raw in {"earphone tip", "earphone tips", "replacement tips", "tips"}:
        return "other"
    padded = f" {raw} "
    for alias in sorted(CATEGORY_ALIASES, key=len, reverse=True):
        if f" {alias} " in padded or raw.startswith(alias + " ") or raw.endswith(" " + alias):
            return CATEGORY_ALIASES[alias]
    tag_rules = (
        ("mousepad", "mousepad"), ("keyboard", "keyboard"), ("keyboards", "keyboard"),
        ("subwoofer", "speaker"), ("monitor speakers", "speaker"), ("speaker", "speaker"),
        ("headphonespro", "headphones"), ("headphone", "headphones"), ("earbud", "headphones"), ("earphone tip", "other"),
        ("in ear monitor", "iem"), ("iem", "iem"), ("earphone", "iem"),
        ("controller", "controller"), ("gamepad", "controller"),
        ("motherboard", "motherboard"), ("graphics card", "gpu"), ("video card", "gpu"),
        ("laptop", "laptop"), ("notebook", "laptop"), ("ultrabook", "laptop"),
        ("netbook", "laptop"), ("2 in 1", "laptop"), ("desktop", "desktop"),
        ("imac", "desktop"), ("mac mini", "desktop"),
        ("cpu", "cpu"), ("processor", "cpu"), ("ram", "ram"), ("memory", "ram"),
        ("ssd", "storage"), ("nvme", "storage"), ("hdd", "storage"),
        ("power supply", "psu"), ("psu", "psu"), ("cooler", "cooler"),
        ("keycap", "keycap"), ("keycaps", "keycap"), ("switch", "switch"), ("switches", "switch"),
        ("clutch pedal", "controller"), ("racing pedal", "controller"),
    )
    padded_tags = re.sub(r"[^a-z0-9]+", " ", raw).strip()
    for token, canonical in tag_rules:
        if re.search(rf"\b{re.escape(token)}\b", padded_tags):
            return canonical
    return raw


def normalize_category(value: Any) -> str:
    """Normalize category labels with cached deterministic alias resolution."""
    return _normalize_category_cached(clean_text(value).casefold())


@lru_cache(maxsize=32768)
def _normalize_title_cached(text: str) -> str:
    text = text.casefold()
    text = re.sub(r"[^a-z0-9+./_-]+", " ", text)
    stop = {
        "buy", "online", "india", "best", "price", "new", "sale", "official",
        "store", "shop", "free", "shipping", "warranty", "the", "and", "with",
        "for", "offer", "offers", "deal", "deals",
    }
    tokens = [t for t in text.split() if len(t) > 1 and t not in stop]
    return " ".join(dict.fromkeys(tokens))


def normalize_title(value: Any) -> str:
    """Canonical title tokens for order-insensitive comparison; cached."""
    return _normalize_title_cached(clean_text(value))


@lru_cache(maxsize=32768)
def _title_tokens_cached(text: str) -> "frozenset[str]":
    return frozenset(normalize_title(text).split())


def title_tokens(value: Any) -> set:
    """Return cached normalized title tokens as a fresh set for callers."""
    return set(_title_tokens_cached(clean_text(value)))


def clean_identifier(value: Any, *, max_len: int = 96) -> str:
    """Generic identifier normalizer preserving meaningful punctuation."""
    s = clean_text(value).upper()
    if not s or s.casefold() in {"", "n/a", "none", "null", "na", "unknown", "-", "--"}:
        return ""
    s = re.sub(r"\s+", "", s)
    s = s[:max_len]
    return s


@lru_cache(maxsize=32768)
def _normalize_mpn_cached(raw: str) -> str:
    s = clean_identifier(raw, max_len=80)
    if not s:
        return ""
    s = re.sub(r"[\u00a0\s]+", "", s).replace("_", "-")
    if s in {"PRODUCT", "MODEL", "SKU", "N/A", "NONE", "NULL"}:
        return ""
    return s


def normalize_mpn(value: Any) -> str:
    """Normalize a manufacturer part number without conflating it with seller identity."""
    return _normalize_mpn_cached(clean_text(value))


@lru_cache(maxsize=32768)
def _normalize_sku_cached(raw: str) -> str:
    return clean_identifier(raw, max_len=80)


def normalize_sku(value: Any) -> str:
    """Normalize seller SKU while preserving retailer-significant punctuation and scope."""
    return _normalize_sku_cached(clean_text(value))


@lru_cache(maxsize=32768)
def _normalize_product_id_cached(raw: str) -> str:
    return clean_identifier(raw, max_len=96)


def normalize_product_id(value: Any) -> str:
    """Normalize a source/entity ID; it remains source-scoped unless proven global."""
    return _normalize_product_id_cached(clean_text(value))


@lru_cache(maxsize=65536)
def _normalize_gtin_cached(raw: str, strict: bool = True) -> str:
    text = _clean_text_cached(raw)
    if not text:
        return ""
    candidate = text.strip()
    labelled = re.fullmatch(
        r"(?:gtin(?:[- ]?(?:8|12|13|14))?|ean(?:[- ]?(?:8|13))?|upc|barcode)\s*[:#=\-]?\s*([0-9][0-9\s-]*)",
        candidate, re.I,
    )
    if labelled:
        candidate = labelled.group(1)
    elif not re.fullmatch(r"[0-9][0-9\s-]*", candidate):
        return ""
    digits = re.sub(r"[\s-]", "", candidate)
    if len(digits) not in {8, 12, 13, 14}:
        return ""
    if len(set(digits)) == 1:
        return ""
    canonical = digits.zfill(14)
    total = 0
    try:
        for idx, ch in enumerate(reversed(canonical)):
            total += int(ch) * (3 if idx % 2 == 1 else 1)
    except ValueError:
        return ""
    if total % 10 == 0:
        return canonical
    return "" if strict else canonical


def normalize_gtin(value: Any, *, strict: bool = True) -> str:
    """Canonicalize GTIN/EAN/UPC to GTIN-14. Strict mode enforces GS1 check digit; lenient mode only preserves numeric shape."""
    if value in (None, ""):
        return ""
    return _normalize_gtin_cached(clean_text(value), bool(strict))


def normalize_identifier(value: Any, kind: str = "generic") -> str:
    """Single public identifier normalization entry point; field-specific wrappers remain semantic owners."""
    k = clean_text(kind).casefold()
    if k == "mpn":
        return normalize_mpn(value)
    if k in {"sku", "seller_sku", "variant_sku"}:
        return normalize_sku(value)
    if k in {"product_id", "entity_id", "variant_id"}:
        return normalize_product_id(value)
    if k == "gtin":
        return normalize_gtin(value)
    return clean_identifier(value)
