#!/usr/bin/env python3
from __future__ import annotations

"""
WooCommerce V175-derived plugin fingerprint + native Google-feed recovery harness.

The attached extract_universal_V175.py is the source/design authority for:
- clearance-aware browser recovery
- persistent-cookie semantics
- browser/XHR discovery
- transport/provenance separation
- bounded recovery budgets
- public-only acquisition

V175 source SHA-256: 33d651b329c20372db40026c0626a3227408096beb910c1d1069266af5cc1b15

This focused harness deliberately does NOT import the 1.5 MB monolith at runtime.
It preserves the V175 evidence contracts while enforcing the repository acceptance boundary:
- Chromium + Firefox/Gecko + WebKit clean browser passes
- public API/XHR discovery without clearance-cookie replay
- optional Cloudflare Browser Run and Browserless adapters
- passive robots/sitemap + historical index discovery
- plugin fingerprint normalization with provenance-aware confidence
- plugin-specific native Google XML candidate generation
- strict payload validation

Important: challenge/clearance encounters are diagnostic only. No clearance cookies, CAPTCHA state,
or anti-bot bypass state are replayed or admitted into native-feed verification.
"""

import asyncio
import gzip
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin, urlsplit, quote

import httpx


TARGETS = [
    ("Aarna Computers", "https://aarnacomputers.com"),
    ("Ads Store", "https://adsstore.in"),
    ("EZPZ Solutions", "https://www.ezpzsolutions.in"),
    ("GamesNComps", "https://gamesncomps.com"),
    ("hotshiftpc", "https://hotshiftpc.com"),
    ("ithunt", "https://ithunt.in"),
    ("KC Computers", "https://kccomputers.co.in"),
    ("KRG KART", "https://krgkart.com"),
    ("Kryptronix Gaming", "https://kryptronix.in"),
    ("NCL Computer", "https://nclcomputer.com"),
    ("PC Kumar Infotech", "https://pckumar.in"),
    ("PCHubShop", "https://www.pchubshop.com"),
    ("Prime ABGB", "https://www.primeabgb.com"),
    ("SCL Gaming", "https://sclgaming.in"),
    ("Variety Infotech", "https://varietyinfotech.com"),
    ("Viper PC", "https://viperpc.in"),
    ("AULA India", "https://aulaindia.com"),
    ("Cosmic Byte", "https://www.thecosmicbyte.com"),
    ("Meckeys", "https://www.meckeys.com"),
    ("StacksKB", "https://stackskb.com"),
    ("Theproaudio", "https://www.theproaudio.com"),
]

KNOWN_10 = {
    "pcstudio.in",
    "quickincomputers.com",
    "avikaretails.com",
    "geekbees.in",
    "ninjadog.in",
    "networkitstore.in",
    "mynexusinfosys.com",
    "solankienterprises.com",
    "onlyssd.com",
    "itgadgetsonline.com",
}

PLUGIN_RULES: List[Tuple[str, Tuple[str, ...]]] = [
    ("woocommerce_google_product_feed", (
        "woocommerce google product feed",
        "woocommerce_gpf",
        "woocommerce-gpf",
        "woocommerce-google-product-feed",
        "google_product_feed",
        "google-product-feed",
        "lw_woocommerce_gpf",
    )),
    ("ctx_feed_webappick", (
        "ctx feed", "ctx-feed", "webappick", "woo_feed", "woo-feed",
        "woo feed", "woo_feed-", "webappick-product-feed-for-woocommerce",
    )),
    ("adtribes_product_feed_pro", (
        "product feed pro", "adtribes", "woo-product-feed-pro",
        "product-feed-pro", "woo-product-feed-pro-for-woocommerce",
    )),
    ("wpfm_product_feed_manager", (
        "product feed manager", "wppfm", "wppfm-feeds", "wpfm/v1",
        "product-feed-manager-for-woocommerce",
    )),
    ("webtoffee_product_feed", (
        "webtoffee", "webtoffee_product_feed", "webtoffee-product-feed",
        "webtoffee-product-feed-for-woocommerce",
    )),
    ("codesolz_merchant_feed_booster", (
        "codesolz", "codesolz-feeds", "merchant feed booster",
        "merchant-feed-booster-lite-for-woocommerce",
    )),
    ("feedcraft", (
        "feedcraft", "feedcraft-product-feed", "thebasics-product-feed",
    )),
    ("google_for_woocommerce", (
        "google-listings-and-ads", "google for woocommerce", "wc/gla",
        "google_merchant_center", "google merchant center",
    )),
]

GENERIC_FEED_PATHS = [
    "/?woocommerce_gpf=google",
    "/woocommerce_gpf/google",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=10",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=50",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=500",
    "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=100",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
    "/woocommerce_gpf/google?gpf_start=0&gpf_limit=1000",
    "/google.xml",
    "/google_feed.xml",
    "/google-feed.xml",
    "/google_base.xml",
    "/googlebase.xml",
    "/google-products.xml",
    "/google-product-feed.xml",
    "/google_product_feed.xml",
    "/google-shopping.xml",
    "/google-shopping-feed.xml",
    "/google-merchant.xml",
    "/google-merchant-feed.xml",
    "/merchant.xml",
    "/merchant-feed.xml",
    "/merchant_feed.xml",
    "/gpf.xml",
    "/product-feed.xml",
    "/products-feed.xml",
    "/feed_products.xml",
    "/feed.xml",
    "/feed/google.xml",
    "/feed/google-feed.xml",
    "/feed/google-products.xml",
    "/feed/google-product-feed.xml",
    "/feed/google-shopping.xml",
    "/feed/google-shopping-feed.xml",
    "/feed/merchant.xml",
    "/feed/merchant-feed.xml",
    "/feeds/google.xml",
    "/feeds/google-feed.xml",
    "/feeds/google-products.xml",
    "/feeds/google-product-feed.xml",
    "/feeds/google-shopping.xml",
    "/feeds/google-shopping-feed.xml",
    "/feeds/merchant.xml",
    "/feeds/merchant-feed.xml",
    "/catalog/feed",
    "/catalog/feed.xml",
    "/catalog/google.xml",
    "/media/feed/google.xml",
    "/wp-content/uploads/google.xml",
    "/wp-content/uploads/google-feed.xml",
    "/wp-content/uploads/google_product_feed.xml",
    "/wp-content/uploads/google-shopping.xml",
    "/wp-content/uploads/codesolz-feeds/google.xml",
    "/wp-content/uploads/codesolz-feeds/google-products.xml",
    "/wp-content/uploads/woo-feed/google.xml",
    "/wp-content/uploads/woo-feed/google/feed.xml",
    "/wp-content/uploads/woo-feed/google/xml/google.xml",
    "/wp-content/uploads/woo-feed/google/xml/google-shopping.xml",
    "/wp-content/uploads/woo-feed/google/xml/feed.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
    "/wp-content/uploads/woo-product-feed-pro/xml/feed.xml",
    "/wp-content/uploads/wppfm-feeds/google.xml",
    "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
    "/wp-json/feedcraft-product-feed/v1/xml",
    "/wp-json/feedcraft-product-feed/v1/google.xml",
    "/wp-json/feedcraft-product-feed/v1/feed.xml",
    "/wp-json/google-product-feed/v1/xml",
    "/wp-json/google-feed/v1/xml",
    "/wp-json/woo-feed/v1/google.xml",
]

PLUGIN_CANDIDATES = {
    "woocommerce_google_product_feed": [
        "/?woocommerce_gpf=google",
        "/woocommerce_gpf/google",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=100",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=250",
        "/?woocommerce_gpf=google&gpf_start=0&gpf_limit=1000",
        "/woocommerce_gpf/google?gpf_start=0&gpf_limit=250",
    ],
    "ctx_feed_webappick": [
        "/?woo_feed=google&wt=xml",
        "/?woo_feed=google_shopping&wt=xml",
        "/?woo_feed=google-shopping&wt=xml",
        "/?woo_feed=google_merchant&wt=xml",
    ],
    "adtribes_product_feed_pro": [
        "/wp-content/uploads/woo-product-feed-pro/xml/google.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-products.xml",
        "/wp-content/uploads/woo-product-feed-pro/xml/google-shopping-feed.xml",
        "/wp-content/uploads/woo-product-feed-pro/google.xml",
    ],
    "wpfm_product_feed_manager": [
        "/wp-content/uploads/wppfm-feeds/google.xml",
        "/wp-content/uploads/wppfm-feeds/google-shopping.xml",
        "/wp-content/uploads/wppfm-feeds/google-feed.xml",
        "/wp-content/uploads/wppfm-feeds/google_products.xml",
    ],
    "webtoffee_product_feed": [
        "/wp-content/uploads/webtoffee_product_feed/wt_Google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google-shopping_Feed.xml",
        "/wp-content/uploads/webtoffee_product_feed/wt_google_shopping_Feed.xml",
    ],
    "codesolz_merchant_feed_booster": [
        "/wp-content/uploads/codesolz-feeds/google.xml",
        "/wp-content/uploads/codesolz-feeds/google-products.xml",
        "/wp-content/uploads/codesolz-feeds/google-shopping.xml",
    ],
    "feedcraft": [
        "/wp-json/feedcraft-product-feed/v1/xml",
        "/wp-json/feedcraft-product-feed/v1/google.xml",
        "/wp-json/feedcraft-product-feed/v1/feed.xml",
        "/wp-json/feedcraft-product-feed/v1/google",
    ],
}

API_PATHS = [
    "/wp-json/",
    "/wp-json/wp/v2/types",
    "/wp-json/wc/store/v1/products?per_page=1",
    "/wp-json/wc/store/v1/products/",
    "/?rest_route=/wc/store/v1/products",
]
WC_REST_PATHS = [
    "/wp-json/wc/v1/products",
    "/wp-json/wc/v2/products",
    "/wp-json/wc/v3/products",
]

MAX_DIRECT_FEED_PROBES = max(10, int(os.getenv("MAX_DIRECT_FEED_PROBES", "40")))
MAX_INTERNAL_PAGES = max(0, min(2, int(os.getenv("MAX_INTERNAL_PAGES", "2"))))
PASSIVE_INDEX_ENABLED = os.getenv("PASSIVE_INDEX_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
WAYBACK_ENABLED = os.getenv("WAYBACK_ENABLED", "1").strip().lower() not in {"0", "false", "no"}
COMMONCRAWL_ENABLED = os.getenv("COMMONCRAWL_ENABLED", "0").strip().lower() in {"1", "true", "yes"}
CF_BROWSER_RUN_ENABLED = os.getenv("CF_BROWSER_RUN_ENABLED", "0").strip().lower() in {"1", "true", "yes"}

PASSIVE_FEED_HINT_RE = re.compile(
    r"(?:feed|google|merchant|shopping|woocommerce_gpf|woo_feed|wppfm|wpfm|webtoffee|adtribes|feedcraft|product-feed)",
    re.I,
)



@dataclass
class BrowserEvidence:
    engine: str
    status: int = 0
    challenge: bool = False
    challenge_encountered: bool = False
    cf_clearance: bool = False
    cookie_names: List[str] = None
    user_agent: str = ""
    html_len: int = 0
    visited_internal_urls: List[str] = None
    plugin_asset_slugs: List[str] = None
    namespaces: List[str] = None
    xhr_urls: List[str] = None
    resource_urls: List[str] = None
    error: str = ""

    def __post_init__(self):
        self.cookie_names = self.cookie_names or []
        self.visited_internal_urls = self.visited_internal_urls or []
        self.plugin_asset_slugs = self.plugin_asset_slugs or []
        self.namespaces = self.namespaces or []
        self.xhr_urls = self.xhr_urls or []
        self.resource_urls = self.resource_urls or []


@dataclass
class ApiEvidence:
    url: str
    status: int
    allow: str = ""
    content_type: str = ""
    namespaces: List[str] = None
    plugin_hits: List[str] = None
    body_read: bool = False
    error: str = ""

    def __post_init__(self):
        self.namespaces = self.namespaces or []
        self.plugin_hits = self.plugin_hits or []
