import hashlib


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def verify_content_hash(content: str, expected_hash: str) -> bool:
    return sha256_text(content) == expected_hash
