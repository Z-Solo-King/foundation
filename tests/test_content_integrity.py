from backend.content_integrity import sha256_text, verify_content_hash


def test_content_hash_round_trip():
    content = "The system stores evidence."
    digest = sha256_text(content)

    assert verify_content_hash(content, digest) is True
    assert verify_content_hash("Changed content.", digest) is False
