from backend.sources.methods import DEFAULT_METHODS


def test_default_acquisition_methods():
    assert len(DEFAULT_METHODS) >= 5
    assert DEFAULT_METHODS[0].name == "direct_http"
    assert all(method.enabled for method in DEFAULT_METHODS)
