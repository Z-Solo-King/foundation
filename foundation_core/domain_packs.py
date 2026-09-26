"""Category-specific spec extraction from already-observed text.

Ported from the legacy V175 extractor's DOMAIN_PACKS layer. This module
does pure regex matching against text you already have (title/description/
spec strings) — it performs no network I/O, no page fetching, and has no
dependency on the acquisition/anti-bot layer. Domain packs are declarative
category rules for keyboard, mouse, mousepad, display, and other India
PC-component/electronics categories.

Not ported: the acquisition-side scoring that blends this with schema-field
evidence and mapper row state (too entangled with the extractor's internal
row-building pipeline to lift cleanly) — this module exposes the
self-contained subset: domain detection + rule application over text.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple

DOMAIN_PACKS: Dict[str, Dict[str, Any]] = {
    'keyboard': {'detect': ('\\bkeyboard(s)?\\b', '\\bmechanical keyboard\\b', '\\bhall effect keyboard\\b', '\\bgaming keyboard\\b', '\\bbarebone keyboard\\b'), 'rules': (('regex', 'layout', '(?:40|60|65|68|75|80|96|98|100)%|\\bTKL\\b|\\b(?:RK61|G61|87|108)\\b', 'layout'), ('map_contains', 'keycap_profile', {'cherry': 'Cherry', 'pbt': 'PBT', 'abs': 'ABS', 'oem': 'OEM', 'mda': 'MDA', 'osa': 'OSA', 'asa': 'ASA', 'xda': 'XDA', 'sa': 'SA'}), ('contains', 'hotswap', ('hot-swap', 'hotswap'), 'Yes'), ('contains_map', 'assembly', (('barebone', 'Barebone'), ('prebuilt', 'Prebuilt'), ('assembled', 'Prebuilt'))), ('measurement', 'weight', '(?<!\\d)(\\d{1,4}(?:\\.\\d+)?)\\s*(g|kg)\\b', 'weight_g'), ('measurement', 'battery', '(?<!\\d)(\\d{2,6})\\s*mAh\\b', 'mAh'), ('multi_contains', 'pins', (('\\b3[- ]?pin\\b', '3-pin'), ('\\b5[- ]?pin\\b', '5-pin'))), ('contains', 'knob_support', ('knob', 'rotary encoder'), 'Yes'), ('contains_map', 'mount_style', (('gasket', 'Gasket'), ('top mount', 'Top'), ('bottom mount', 'Bottom'), ('plate', 'Plate'), ('tray', 'Tray'), ('sandwich', 'Sandwich'), ('pcb mount', 'PCB'))), ('multi_material', 'case_material', ('abs', 'aluminum', 'polycarbonate', 'acrylic', 'wood', 'silicone', 'steel', 'copper')), ('measurement', 'polling_rate', '(?<!\\d)(\\d{3,5})\\s*Hz\\b', 'Hz'), ('multi_contains', 'connection_type', (('\\bbluetooth\\b', 'Bluetooth'), ('\\bwireless\\b|\\b2\\.?4\\s*ghz\\b', 'Wireless'), ('\\bwired\\b|\\busb\\b', 'Wired'))), ('contains_map', 'keyboardproduct_type', (('hall effect', 'Hall Effect Keyboard'), ('mechanical', 'Mechanical Keyboard'))))},
    'mouse': {'detect': ('\\bmice\\b', '\\bmouse\\b', '\\bgaming mouse\\b', '\\bwireless mouse\\b'), 'rules': (('map_contains', 'tracking_method', {'bamf 3.0': 'PAW3950', 'bamf 2.0': 'PAW3395', 'xs-1': 'PAW3950', 'focus pro': 'PAW3950', '26k': 'PAW3395', '4g hero': 'HERO', '5g hero': 'HERO'}), ('regex', 'tracking_method', '\\bPAW\\d{3,4}(?:\\s*(?:HS|SE|MAX|ULTRA|MASTER))?\\b', 'identity'), ('measurement', 'weight', '(?<!\\d)(\\d{1,4}(?:\\.\\d+)?)\\s*g\\b', 'g'), ('special_weight_6369', 'weight', 'IPI Haze 6369g → 63/69g', 'weight_g'), ('measurement', 'battery', '(?<!\\d)(\\d{2,6})\\s*mAh\\b', 'mAh'), ('dpi', 'maximum_dpi', '(?<!\\d)(\\d{1,3})\\s*K\\s*(?:DPI)?\\b|(?<!\\d)(\\d{4,6})\\s*DPI\\b'), ('multi_contains', 'connection_type', (('\\bbluetooth\\b|\\bbt\\b', 'Wireless BT'), ('\\b2\\.?4\\s*(?:ghz)?\\b|\\bwireless\\b', 'Wireless 2.4 GHZ'), ('\\bwired\\b|\\busb\\b', 'Wired'))), ('contains_map', 'switch_type', (('d2fc-f-7n', 'Omron D2FC-F-7N 100M'), ('omron', 'Omron Mechanical'), ('optical', 'Optical'), ('huano green shell', 'Huano Green Shell White Dot'), ('huano blue shell', 'Huano Blue Shell Pink Dot'), ('ttc gold', 'TTC Gold'), ('kailh', 'Kailh'))), ('multi_contains', 'grip_type', (('palm', 'Palm'), ('claw', 'Claw'), ('fingertip', 'Fingertip'))))},
    'audio': {'detect': ('\\biem\\b', '\\bin-ear\\b', '\\bearphone(s)?\\b', '\\bheadphones?\\b', '\\bheadset\\b', '\\bspeakers?\\b', '\\bsoundbar\\b'), 'rules': ()},
    'display': {'detect': ('\\bmonitor\\b', '\\bdisplay\\b', '\\btelevision\\b', '\\btv\\b'), 'rules': (('measurement', 'refresh_rate', '(?<!\\d)(\\d{2,4})\\s*Hz\\b', 'Hz'),)},
    'storage': {'detect': ('\\bssd\\b', '\\bhdd\\b', '\\bsolid state\\b', '\\bhard drive\\b'), 'rules': ()},
    'camera': {'detect': ('\\bcamera\\b', '\\bwebcam\\b', '\\bmirrorless\\b', '\\bdslr\\b'), 'rules': ()},
    'networking': {'detect': ('\\brouter\\b', '\\bswitch\\b', '\\baccess point\\b', '\\bnetwork adapter\\b'), 'rules': ()},
    'mousepad': {'detect': ('\\bmouse ?pad(s)?\\b', '\\bdesk ?mat(s)?\\b', '\\bmousemat(s)?\\b'), 'rules': (
        ('contains_map', 'mousepad_speed', (('extremely fast', 'Extremely fast'), ('very fast', 'Very fast'), ('fast', 'Fast'), ('quick', 'Quick'), ('balanced', 'Balanced'), ('control', 'Control'), ('slow', 'Slow'), ('very slow', 'Very slow'), ('extremely slow', 'Extremely slow'))),
        ('contains_map', 'mousepad_texture', (('rough', 'Rough'), ('textured', 'Textured'), ('smooth', 'Smooth'))),
        ('contains_map', 'mousepad_firmness', (('very soft', 'Very soft'), ('soft', 'Soft'), ('firm', 'Firm'), ('very firm', 'Very firm'), ('hard', 'Hard'))),
        ('measurement', 'thickness_mm', '(?<!\\d)(\\d+(?:\\.\\d+)?)\\s*mm\\b', 'mm'),
    )},
    'computer': {'detect': ('\\blaptop\\b', '\\bnotebook\\b', '\\bdesktop\\b', '\\bprebuilt\\b', '\\bmini pc\\b'), 'related_domains': ('display', 'storage'), 'rules': ()},
}

_COMPILED_DOMAIN_DETECT: Dict[str, Tuple[Any, ...]] = {
    str(name): tuple(re.compile(str(pattern), re.I) for pattern in (pack.get("detect", ()) or ()))
    for name, pack in DOMAIN_PACKS.items()
    if isinstance(pack, dict)
}


def detect_domains(text: str, category_text: str = "") -> List[str]:
    """Score domain packs against free text (and optionally a category string),
    returning matching domain names ordered by descending match strength.

    Category-text hits are weighted higher than body-text hits, mirroring the
    source engine's preference for explicit category signal over incidental
    keyword mentions.
    """
    scored: List[Tuple[int, str]] = []
    for domain_name, detectors in _COMPILED_DOMAIN_DETECT.items():
        score = sum(1 for pattern in detectors if pattern.search(text))
        if category_text:
            score += 2 * sum(1 for pattern in detectors if pattern.search(category_text))
        if score:
            scored.append((score, domain_name))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [name for _, name in scored]


def related_domains(domains: Iterable[str]) -> List[str]:
    """Domains related to the matched set (e.g. 'computer' relates to 'display'/'storage')."""
    out: List[str] = []
    matched = set(domains)
    for name in domains:
        pack = DOMAIN_PACKS.get(name, {})
        for related in pack.get("related_domains", ()):
            if related in DOMAIN_PACKS and related not in matched and related not in out:
                out.append(related)
    return out


def apply_domain_rules(text: str, domains: Iterable[str], *, device_text: str = "") -> Dict[str, str]:
    """Apply domain-pack rules against text, returning newly-inferred fields.

    ``text`` should be lowercased already-observed text (title + description +
    spec sheet, concatenated) used for substring/contains-style rules.
    ``device_text`` is the original-case text used for regex/measurement rules
    that need exact digit/unit matches; defaults to ``text`` if not supplied.
    First rule to produce a field wins — later rules never overwrite an
    already-set field, matching the source engine's precedence.
    """
    device_text = device_text or text
    out: Dict[str, str] = {}

    def put_if_missing(key: str, value: Any) -> None:
        value = str(value).strip() if value is not None else ""
        if value and not out.get(key):
            out[key] = value[:200]

    for domain_name in domains:
        pack = DOMAIN_PACKS.get(domain_name, {})
        for rule in pack.get("rules", ()):
            kind = rule[0]
            if kind == "map_contains":
                _, field, mapping = rule
                for token, value in mapping.items():
                    if token in text:
                        put_if_missing(field, value)
                        break
            elif kind == "contains":
                _, field, needles, value = rule
                if any(n in text for n in needles):
                    put_if_missing(field, value)
            elif kind == "contains_map":
                _, field, pairs = rule
                for token, value in pairs:
                    if token in text:
                        put_if_missing(field, value)
                        break
            elif kind == "regex":
                _, field, pattern, transform = rule
                m = re.search(pattern, device_text, re.I)
                if m:
                    raw_value = re.sub(r"\s+", " ", m.group(0)).strip()
                    if transform == "layout":
                        t = raw_value.upper()
                        value = "75%" if t == "TKL" else (f"{t}%" if t.isdigit() else t)
                    else:
                        value = raw_value
                    put_if_missing(field, value)
            elif kind == "measurement":
                _, field, pattern, unit = rule
                m = re.search(pattern, device_text, re.I)
                if not m:
                    continue
                if unit == "weight_g":
                    n = float(m.group(1))
                    value = f"{int(n * 1000) if m.group(2).lower() == 'kg' else int(n)}g"
                elif unit == "Hz":
                    value = f"{m.group(1)} Hz"
                elif unit == "mAh":
                    value = f"{m.group(1)} mAh"
                else:
                    value = f"{m.group(1)}{unit}"
                put_if_missing(field, value)
            elif kind == "multi_contains":
                _, field, pairs = rule
                vals = []
                for pattern, value in pairs:
                    if re.search(pattern, text, re.I):
                        vals.append(value)
                if vals:
                    put_if_missing(field, ", ".join(dict.fromkeys(vals)))
            elif kind == "multi_material":
                _, field, materials = rule
                vals = [m.title() for m in materials if re.search(r"\b" + re.escape(m) + r"\b", text, re.I)]
                if vals:
                    put_if_missing(field, ", ".join(dict.fromkeys(vals)))
            elif kind == "dpi":
                _, field, pattern = rule
                m = re.search(pattern, device_text, re.I)
                if m:
                    n = int(m.group(1) or m.group(2))
                    put_if_missing(field, str(n * (1000 if m.group(1) else 1)))
            elif kind == "special_weight_6369":
                if "6369g" in text or "6369 g" in text:
                    if "ipi" in text and "haze" in text:
                        value = "69g" if any(x in text for x in (" tmr", "haze x1", "haze x ii")) else "63g"
                        put_if_missing("weight", value)
    return out
