def test_choose_method_skips_disabled_before_enabled(monkeypatch):
    import backend.execution.acquisition as acquisition
    from backend.intelligence.sources import Source, SourcePolicy, SourceType
    from backend.sources.methods import AcquisitionMethod

    source = Source("s", "https://example.com", SourceType.WEB)
    disabled = AcquisitionMethod("disabled", "x", enabled=False)
    enabled = AcquisitionMethod("enabled", "x", enabled=True)
    monkeypatch.setattr(acquisition, "DEFAULT_METHODS", (disabled, enabled))
    assert acquisition.choose_method(source, SourcePolicy()).name == "enabled"
