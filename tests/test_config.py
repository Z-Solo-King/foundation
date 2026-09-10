from backend.core.config import settings

def test_settings():
    assert settings.app_name == "Research Intelligence Engine"
    assert settings.version == "0.1.0"
