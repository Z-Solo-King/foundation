"""Compatibility exports for content-integrity helpers.

The canonical implementation lives in ``backend.content_integrity``.
Keep this module as a thin compatibility surface so existing imports do not
create a second implementation.
"""

from backend.content_integrity import sha256_text, verify_content_hash

__all__ = ["sha256_text", "verify_content_hash"]
