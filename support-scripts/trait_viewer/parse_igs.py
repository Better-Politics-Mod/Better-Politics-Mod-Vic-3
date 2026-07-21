"""
Parses better-politics-mod/common/scripted_effects/bpm_aa_interest_group_ideology_setter.txt
for every usage of bpm_apply_traits_ig, and produces a JSON-friendly structure mapping
each interest group to the trait it uses per category (gov/exe/dop/sta/.../vanilla).

Cross-checks each referenced trait against the traits already parsed by parse_traits.py
so a typo'd or removed trait name shows up as a warning instead of failing silently.

Usage:
    python3 parse_igs.py
"""

import base64
import json
import os
import shutil
import subprocess

from parse_traits import (
    CATEGORY_ORDER,
    parse_document,
    build_traits,
    INPUT_PATH as TRAITS_INPUT_PATH,
)

CWD = os.path.dirname(os.path.abspath(__file__))
INPUT_PATH = os.path.join(
    CWD, "..", "..", "better-politics-mod", "common", "scripted_effects",
    "bpm_aa_interest_group_ideology_setter.txt",
)
TEMPLATE_PATH = os.path.join(CWD, "ig_viewer_template.html")
OUTPUT_PATH = os.path.join(CWD, "ig_viewer.html")
ICONS_DIR = os.path.join(CWD, "..", "..", "better-politics-mod", "gfx", "interface", "icons", "ig_icons")

APPLY_KEY = ["bpm_apply_traits_ig", "bpm_apply_traits_ig_deactivatable"]


_IMAGEMAGICK_BIN = shutil.which("magick") or shutil.which("convert")
_icon_cache = {}

ICON_FILENAME_OVERRIDES = {
    "intelligentsia": "intelligensia",
    "revolutionist_socialists": "revolutionists",
    "reformist_socialists": "reformists"
}

def get_icon_data_uri(ig_name, small):
    if not _IMAGEMAGICK_BIN:
        return None
    basename = ICON_FILENAME_OVERRIDES.get(ig_name, ig_name)
    filename = f"{basename}_30.dds" if small else f"{basename}.dds"
    cache_key = filename
    if cache_key in _icon_cache:
        return _icon_cache[cache_key]

    path = os.path.join(ICONS_DIR, filename)
    if not os.path.isfile(path):
        _icon_cache[cache_key] = None
        return None

    try:
        result = subprocess.run(
            [_IMAGEMAGICK_BIN, path, "PNG:-"],
            capture_output=True, check=True,
        )
        data_uri = "data:image/png;base64," + base64.b64encode(result.stdout).decode("ascii")
    except (subprocess.CalledProcessError, OSError):
        data_uri = None

    _icon_cache[cache_key] = data_uri
    return data_uri


def find_entry(entries, key):
    for e in entries:
        if e["k"] == key:
            return e
    return None


def find_apply_traits(entries, condition=None):
    """Recursively find every bpm_apply_traits_ig = { ... } block, carrying along
    the nearest enclosing if/else_if/else `limit` condition it's gated behind (if any)."""
    results = []
    limit_entry = find_entry(entries, "limit")
    local_condition = limit_entry["v"] if (limit_entry and isinstance(limit_entry["v"], list)) else condition

    for e in entries:
        if e["k"] in APPLY_KEY and isinstance(e["v"], list):
            results.append({"entries": e["v"], "condition": local_condition})
        elif isinstance(e["v"], list):
            if e["k"] in ("if", "else_if", "else"):
                results.extend(find_apply_traits(e["v"], local_condition))
            else:
                results.extend(find_apply_traits(e["v"], None))
    return results


def build_igs(root_entries, known_traits):
    igs = []
    warnings = []

    for e in root_entries:
        if not e["k"].startswith("bpm_update_ideology_") or not isinstance(e["v"], list):
            continue
        source_effect = e["k"]

        for occurrence in find_apply_traits(e["v"]):
            fields = {sub["k"]: sub["v"] for sub in occurrence["entries"] if isinstance(sub["v"], str)}
            ig_name = fields.get("ig")
            if not ig_name:
                warnings.append(f"'{source_effect}' has a {", ".join(APPLY_KEY)} block with no 'ig = ...' field; skipped.")
                continue

            categories = {}
            for cat in CATEGORY_ORDER:
                value = fields.get(cat)
                if value is None:
                    categories[cat] = {"status": "unset", "value": None, "trait": None}
                elif value == "TODO":
                    categories[cat] = {"status": "todo", "value": value, "trait": None}
                else:
                    trait_name = f"bpm_trait_{cat}_{value}"
                    if trait_name not in known_traits:
                        warnings.append(
                            f"IG '{ig_name}' ({source_effect}): {cat} = {value} -> "
                            f"'{trait_name}' does not exist in the traits file."
                        )
                        categories[cat] = {"status": "missing", "value": value, "trait": trait_name}
                    elif value == "none":
                        categories[cat] = {"status": "none", "value": value, "trait": trait_name}
                    else:
                        categories[cat] = {"status": "trait", "value": value, "trait": trait_name}

            igs.append({
                "ig": ig_name,
                "sourceEffect": source_effect,
                "condition": occurrence["condition"],
                "categories": categories,
                "iconSmall": get_icon_data_uri(ig_name, small=True),
                "iconLarge": get_icon_data_uri(ig_name, small=False),
            })

    if not _IMAGEMAGICK_BIN:
        warnings.append("ImageMagick ('magick'/'convert') not found on PATH; IG icons will be skipped.")

    return igs, warnings


def main():
    with open(TRAITS_INPUT_PATH, "r", encoding="utf-8") as f:
        traits_text = f.read()
    traits_data = build_traits(parse_document(traits_text))
    known_traits = set(traits_data["traits"].keys())

    with open(INPUT_PATH, "r", encoding="utf-8") as f:
        text = f.read()
    root_entries = parse_document(text)

    igs, warnings = build_igs(root_entries, known_traits)

    print(f"Parsed {len(igs)} interest groups using {", ".join(APPLY_KEY)}.")
    for w in warnings:
        print(f"  WARNING: {w}")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()

    payload = json.dumps({"igs": igs, "categoryOrder": CATEGORY_ORDER}, ensure_ascii=False)
    out = template.replace("__IGS_DATA__", payload)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(out)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
