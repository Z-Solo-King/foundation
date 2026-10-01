#!/usr/bin/env python3
"""Compatibility facade for the WooCommerce V175 recovery harness.

The legacy import/CLI surface is preserved while implementation responsibilities
are split into contracts, discovery/validation, public transport/advisory, and
site execution.
"""
from __future__ import annotations

import asyncio

try:
    from tools.woocommerce_v175_contracts import *
    from tools.woocommerce_v175_discovery import *
    from tools.woocommerce_v175_transport import *
    from tools.woocommerce_v175_runner import *
except ModuleNotFoundError:
    from woocommerce_v175_contracts import *
    from woocommerce_v175_discovery import *
    from woocommerce_v175_transport import *
    from woocommerce_v175_runner import *

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
