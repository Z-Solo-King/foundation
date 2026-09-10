from backend.models.common import Timestamped


def test_timestamped():
    item = Timestamped.now()
    assert item.created_at.tzinfo is not None
