"""
Regenerates the mod's blanked copies of vanilla content:
- better-politics-mod/common/ideologies/zz_00_ig_ideologies.txt replaces every vanilla IG
  ideology with a blank version that keeps only its icon, and the
  bpm_set_vanilla_ideologies_list scripted effect is rewritten to list the same ideologies.
- better-politics-mod/common/political_movements/zz_00_vanilla_movements.txt replaces every
  vanilla political movement with a version that can never be created or supported.
  The mod's own movement files load after it, so any it redefines still take effect.
- better-politics-mod/common/ideologies/zz_bpm_vanilla_leader_ideologies.txt replaces every
  vanilla leader ideology with a version no character can be given. It loads after the
  vanilla files but before the mod's bpm_* files, so any the mod redefines still take effect.

Vanilla IG ideologies the mod already defines or replaces in its own files are left alone.

Usage: python blank_vanilla_ig_ideologies.py [path/to/Victoria 3/game]
"""
import re
import sys
from pathlib import Path

DEFAULT_GAME_DIR = Path.home() / ".local/share/Steam/steamapps/common/Victoria 3/game"
# Vanilla IG ideologies live in the 00_* files; 01-03 are character and movement ideologies
VANILLA_IDEOLOGIES_GLOB = "00_*.txt"
VANILLA_LEADER_IDEOLOGIES_GLOB = "*.txt"
LEADER_IDEOLOGY_EXCEPTIONS = {"ideology_moderate", "ideology_child"}
VANILLA_MOVEMENTS_GLOB = "*.txt"
MOVEMENT_EXCEPTIONS = {"movement_cultural_minority"}

MOD_COMMON_DIR = Path(__file__).resolve().parent.parent / "better-politics-mod/common"
MOD_IDEOLOGIES_DIR = MOD_COMMON_DIR / "ideologies"
IDEOLOGIES_OUTPUT_FILE = MOD_IDEOLOGIES_DIR / "zz_00_ig_ideologies.txt"
LEADER_IDEOLOGIES_OUTPUT_FILE = MOD_IDEOLOGIES_DIR / "zz_bpm_vanilla_leader_ideologies.txt"
MOVEMENTS_OUTPUT_FILE = MOD_COMMON_DIR / "political_movements/zz_00_vanilla_movements.txt"
EFFECTS_FILE = MOD_COMMON_DIR / "scripted_effects/bpm_global_init_effects.txt"
VANILLA_LIST_EFFECT_RE = re.compile(r'^bpm_set_vanilla_ideologies_list = \{\n.*?^\}', re.MULTILINE | re.DOTALL)

IDEOLOGIES_HEADER = """ideology_nonexistent = {
	icon = "gfx/interface/icons/ideology_icons/placeholder.dds"
}
"""

TOKEN_RE = re.compile(r'#[^\n]*|"[^"]*"|[{}=]|[^\s{}="#]+')
TOP_LEVEL_RE = re.compile(r'^(?:\w+:)?(\w+)\s*=\s*\{', re.MULTILINE)


def parse_top_level(text, keys):
    """Returns [(name, {key: value})] for each top-level block, holding the given depth-1 simple values."""
    tokens = [t for t in TOKEN_RE.findall(text) if not t.startswith("#")]
    entries = []
    depth = 0
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "{":
            depth += 1
        elif tok == "}":
            depth -= 1
        elif depth == 0 and i + 2 < len(tokens) and tokens[i + 1] == "=" and tokens[i + 2] == "{":
            entries.append((tok, {}))
        elif depth == 1 and tok in keys and i + 2 < len(tokens) and tokens[i + 1] == "=" and tokens[i + 2] != "{":
            entries[-1][1][tok] = tokens[i + 2]
            i += 2
        i += 1
    if depth != 0:
        raise ValueError("unbalanced braces")
    return entries


def mod_defined(mod_dir, output_file):
    """Top-level entries the mod defines or replaces in its own files, which must not be clobbered."""
    names = set()
    for path in mod_dir.glob("*.txt"):
        if path == output_file:
            continue
        text = path.read_text(encoding="utf-8-sig")
        names.update(TOP_LEVEL_RE.findall(text))
    return names


def vanilla_entries(vanilla_dir, glob, keys, skip=frozenset()):
    """Yields (name, values) for each vanilla entry not in skip, in load order."""
    vanilla_files = sorted(vanilla_dir.glob(glob))
    if not vanilla_files:
        sys.exit(f"No {glob} files found in {vanilla_dir}")
    seen = set()
    for path in vanilla_files:
        text = path.read_text(encoding="utf-8-sig")
        for name, values in parse_top_level(text, keys):
            if name in seen:
                continue
            seen.add(name)
            if name in skip:
                print(f"Skipping {name}")
                continue
            yield name, values


def update_vanilla_ideologies_list(names):
    text = EFFECTS_FILE.read_text(encoding="utf-8-sig")
    lines = "".join(
        f"\tadd_to_global_variable_list = {{ name = bpm_vanilla_ideologies target = ideology:{name} }}\n"
        for name in names
    )
    text, count = VANILLA_LIST_EFFECT_RE.subn(
        lambda _: f"bpm_set_vanilla_ideologies_list = {{\n{lines}}}", text, count=1
    )
    if count != 1:
        sys.exit(f"bpm_set_vanilla_ideologies_list not found in {EFFECTS_FILE}")
    EFFECTS_FILE.write_text(text, encoding="utf-8-sig")
    print(f"Wrote {len(names)} ideologies to bpm_set_vanilla_ideologies_list in {EFFECTS_FILE}")


def blank_ideologies(game_dir):
    skip = mod_defined(MOD_IDEOLOGIES_DIR, IDEOLOGIES_OUTPUT_FILE)
    blocks = [IDEOLOGIES_HEADER]
    blanked = []
    entries = vanilla_entries(game_dir / "common/ideologies", VANILLA_IDEOLOGIES_GLOB, {"icon"}, skip)
    for name, values in entries:
        blanked.append(name)
        if "icon" not in values:
            print(f"Warning: {name} has no icon")
            blocks.append(f"REPLACE:{name} = {{\n}}\n")
        else:
            blocks.append(f"REPLACE:{name} = {{\n\ticon = {values['icon']}\n}}\n")

    IDEOLOGIES_OUTPUT_FILE.write_text("\n".join(blocks), encoding="utf-8-sig")
    print(f"Wrote {len(blanked)} blanked ideologies to {IDEOLOGIES_OUTPUT_FILE}")

    update_vanilla_ideologies_list(blanked)


def blank_leader_ideologies(game_dir):
    blocks = []
    keys = {"icon", "character_ideology"}
    entries = vanilla_entries(game_dir / "common/ideologies", VANILLA_LEADER_IDEOLOGIES_GLOB, keys, LEADER_IDEOLOGY_EXCEPTIONS)
    for name, values in entries:
        if values.get("character_ideology") != "yes":
            continue
        if "icon" not in values:
            sys.exit(f"{name} has no icon")
        blocks.append(
            f"REPLACE:{name} = {{\n"
            f"\ticon = {values['icon']}\n"
            f"\tshow_in_list = no\n"
            f"\tcharacter_ideology = yes\n"
            f"\tinterest_group_leader_trigger = {{ always = no }}\n"
            f"\tinterest_group_leader_weight = {{ value = 0 }}\n"
            f"\tnon_interest_group_leader_trigger = {{ always = no }}\n"
            f"\tnon_interest_group_leader_weight = {{ value = 0 }}\n"
            f"}}\n"
        )

    LEADER_IDEOLOGIES_OUTPUT_FILE.write_text("\n".join(blocks), encoding="utf-8-sig")
    print(f"Wrote {len(blocks)} blanked leader ideologies to {LEADER_IDEOLOGIES_OUTPUT_FILE}")


def blank_movements(game_dir):
    blocks = []
    entries = vanilla_entries(game_dir / "common/political_movements", VANILLA_MOVEMENTS_GLOB, {"category", "ideology"}, MOVEMENT_EXCEPTIONS)
    for name, values in entries:
        if "category" not in values or "ideology" not in values:
            sys.exit(f"{name} is missing a category or ideology")
        blocks.append(
            f"REPLACE:{name} = {{\n"
            f"\tcategory = {values['category']}\n"
            f"\tideology = {values['ideology']}\n"
            f"\tcreation_trigger = {{ always = no }}\n"
            f"\tcreation_weight = {{ value = 0 }}\n"
            f"\tdisband_trigger = {{ always = yes }}\n"
            f"\tcharacter_support_trigger = {{ always = no }}\n"
            f"\tpop_support_trigger = {{ always = no }}\n"
            f"}}\n"
        )

    MOVEMENTS_OUTPUT_FILE.write_text("\n".join(blocks), encoding="utf-8-sig")
    print(f"Wrote {len(blocks)} blanked movements to {MOVEMENTS_OUTPUT_FILE}")


def main():
    game_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_GAME_DIR
    blank_ideologies(game_dir)
    blank_leader_ideologies(game_dir)
    blank_movements(game_dir)


if __name__ == "__main__":
    main()
