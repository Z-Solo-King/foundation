from foundation_core.text_normalization import (
    _normalize_gtin_cached,
    clean_identifier,
    clean_text,
    normalize_brand,
    normalize_category,
    normalize_gtin,
    normalize_identifier,
    normalize_mpn,
    normalize_product_id,
    normalize_sku,
    normalize_title,
    title_tokens,
)

def test_clean_text_and_brand_normalization():
    assert clean_text(None) == ""
    assert clean_text("  A\u2013B &amp; C  ") == "A-B & C"
    assert normalize_brand("  ASUS-  ") == "asus"
    assert normalize_brand("  ASUSTEK  ") == "asus"
    assert normalize_brand("Unknown Maker") == "unknown maker"

def test_category_exact_accessory_alias_tag_and_fallback():
    assert normalize_category("") == ""
    assert normalize_category("GPU") == "gpu"
    assert normalize_category("Earphone Tips") == "other"
    assert normalize_category("Gaming Laptop Bag") == "laptop"
    assert normalize_category("Bluetooth Keyboard") == "keyboard"
    assert normalize_category("keycap") == "keycap"
    assert normalize_category("headphonespro") == "headphones"
    assert normalize_category("clutch pedal") == "controller"
    assert normalize_category("Mystery Gadget") == "mystery gadget"

def test_title_and_token_normalization():
    assert normalize_title("Buy ASUS TUF 4060 Online India!") == "asus tuf 4060"
    assert title_tokens("ASUS TUF 4060") == {"asus", "tuf", "4060"}

def test_identifier_wrappers_and_limits():
    assert clean_identifier(None) == ""
    assert clean_identifier("N/A") == ""
    assert clean_identifier("ab c_d", max_len=4) == "ABC_"
    assert normalize_mpn(" Model ") == ""
    assert normalize_mpn(None) == ""
    assert normalize_mpn(" ab_c 12 ") == "AB-C12"
    assert normalize_sku(" sku 42 ") == "SKU42"
    assert normalize_product_id(" id 42 ") == "ID42"
    assert normalize_identifier("AB_C", "mpn") == "AB-C"
    assert normalize_identifier("SKU 42", "seller_sku") == "SKU42"
    assert normalize_identifier("ID 42", "entity_id") == "ID42"
    assert normalize_identifier("other", "generic") == "OTHER"

def test_gtin_validation_and_lenient_mode(monkeypatch):
    assert normalize_gtin(None) == ""
    assert _normalize_gtin_cached("") == ""
    assert normalize_gtin("") == ""
    assert normalize_gtin("ean13: 4006381333931") == "04006381333931"
    assert normalize_gtin("036000291452") == "00036000291452"
    assert normalize_gtin("12345678901234") == ""
    assert normalize_gtin("11111111") == ""
    assert normalize_gtin("not-a-gtin") == ""
    assert normalize_gtin("12345678") == ""
    assert normalize_gtin("123456789") == ""
    assert normalize_gtin("12345678", strict=False) == "00000012345678"
    import foundation_core.text_normalization as module
    real_int = module._BUILTIN_INT
    def raising_int(value, *args, **kwargs):
        if value == "1":
            raise ValueError("forced test path")
        return real_int(value, *args, **kwargs)
    monkeypatch.setattr(module, "_BUILTIN_INT", raising_int)
    module._normalize_gtin_cached.cache_clear()
    assert module._normalize_gtin_cached("12345670", True) == ""
    module._normalize_gtin_cached.cache_clear()

def test_identifier_kind_aliases():
    for kind in ("sku","variant_sku","product_id","variant_id"):
        assert normalize_identifier("A1", kind) == "A1"
    assert normalize_identifier("00000013", "gtin") == ""
