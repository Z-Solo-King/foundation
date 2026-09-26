from foundation_core.domain_packs import apply_domain_rules, detect_domains, related_domains

def test_detect_domains_weights_category_hits_and_sorting():
    domains = detect_domains("gaming keyboard and monitor", "keyboard")
    assert domains[0] == "keyboard"
    assert "display" in domains
    assert detect_domains("nothing relevant") == []

def test_related_domains_is_deduplicated_and_ordered():
    assert related_domains(["computer"]) == ["display", "storage"]
    assert related_domains(["computer", "display"]) == ["storage"]
    assert related_domains(["unknown"]) == []

def test_keyboard_domain_rules_cover_all_rule_kinds():
    text = "tkl pbt hot-swap prebuilt 1.25 kg 3000 mah 3-pin knob gasket abs 1000 hz bluetooth hall effect"
    out = apply_domain_rules(text, ["keyboard"])
    assert out == {
        "layout": "75%",
        "keycap_profile": "PBT",
        "hotswap": "Yes",
        "assembly": "Prebuilt",
        "weight": "1250g",
        "battery": "3000 mAh",
        "pins": "3-pin",
        "knob_support": "Yes",
        "mount_style": "Gasket",
        "case_material": "Abs",
        "polling_rate": "1000 Hz",
        "connection_type": "Bluetooth",
        "keyboardproduct_type": "Hall Effect Keyboard",
    }

def test_mouse_and_display_rules_cover_regex_measurement_dpi_and_maps():
    mouse = apply_domain_rules("bamf 3.0 68 g 2000 mah 26k dpi bluetooth omron palm", ["mouse"])
    assert mouse["tracking_method"] == "PAW3950"
    assert mouse["weight"] == "68g"
    assert mouse["battery"] == "2000 mAh"
    assert mouse["maximum_dpi"] == "26000"
    assert mouse["connection_type"] == "Wireless BT"
    assert mouse["switch_type"] == "Omron Mechanical"
    assert mouse["grip_type"] == "Palm"
    assert apply_domain_rules("27 inch monitor", ["display"]) == {}
    assert apply_domain_rules("27 inch monitor 165 hz", ["display"])["refresh_rate"] == "165 Hz"

def test_mousepad_rules_and_special_weight():
    pad = apply_domain_rules("mousepad very fast textured very soft 4 mm", ["mousepad"])
    assert pad == {
        "mousepad_speed": "Very fast",
        "mousepad_texture": "Textured",
        "mousepad_firmness": "Very soft",
        "thickness_mm": "4mm",
    }
    special = apply_domain_rules("ipi haze 6369g haze x1", ["mouse"])
    assert special["weight"] == "69g"

def test_first_rule_wins_and_device_text_override():
    out = apply_domain_rules("1 kg 1000 hz", ["keyboard", "mouse"], device_text="TKL 1 kg 1000 Hz")
    assert out["layout"] == "75%"
    assert out["weight"] == "1000g"
    assert out["polling_rate"] == "1000 Hz"

def test_unmatched_and_alternate_transform_paths():
    assert apply_domain_rules("9g wired", ["mouse"])["weight"] == "9g"
    assert apply_domain_rules("16000 DPI wired", ["mouse"])["maximum_dpi"] == "16000"
    assert apply_domain_rules("5-pin wired aluminum", ["keyboard"])["pins"] == "5-pin"
    assert apply_domain_rules("sandwich wireless", ["keyboard"])["mount_style"] == "Sandwich"
    assert apply_domain_rules("switch wireless", ["keyboard"])["connection_type"] == "Wireless"
    assert apply_domain_rules("usb", ["keyboard"])["connection_type"] == "Wired"


def test_special_weight_negative_branches_are_noops():
    assert apply_domain_rules("mouse", ["mouse"]) == {}
    assert apply_domain_rules("ipi haze 6368g standard", ["mouse"])["weight"] == "6368g"
    assert apply_domain_rules("6369g standard mouse", ["mouse"])["weight"] == "6369g"


def test_regex_identity_and_special_weight_alternate_branch():
    assert apply_domain_rules("paw3395 wired", ["mouse"])["tracking_method"] == "paw3395"
    assert apply_domain_rules("ipi haze 6369g standard", ["mouse"])["weight"] == "63g"
    assert apply_domain_rules("ipi haze 6369g haze x1 tmr", ["mouse"])["weight"] == "69g"
