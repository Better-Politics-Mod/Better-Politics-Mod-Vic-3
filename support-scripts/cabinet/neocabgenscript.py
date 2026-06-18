import json
from collections import defaultdict

# -----------------------
# Load files
# -----------------------

with open("support-scripts/cabinet/institution_lawgroup.json", encoding="utf8") as f:
    institution_lawgroup = json.load(f)

with open("support-scripts/cabinet/modifiers.json", encoding="utf8") as f:
    modifiers = json.load(f)

with open("support-scripts/cabinet/ministry.json", encoding="utf8") as f:
    ministry_map = json.load(f)

# -----------------------
# Group institutions by ministry
# -----------------------

ministries = defaultdict(list)
for institution, ministry in ministry_map.items():
    ministries[ministry].append(institution)

# -----------------------
# Collect all IG keys
# -----------------------

ig_keys = set()

for inst_mods in modifiers.values():
    for modname, igs in inst_mods.items():
        if modname == "":
            continue
        ig_keys.update(igs)

ig_keys = sorted(ig_keys)

f = "better-politics-mod/common/scripted_effects/bpm_neocabgenscript.txt"

with open(f, "w", encoding="utf8") as out:

    # =========================================================
    # RELOAD / ADD AMENDMENTS
    # =========================================================

    out.write("bpm_reload_institution_amendments = {\n\n")

    for ministry in sorted(ministries):

        out.write(f"\t# {ministry}\n\n")

        for ig in ig_keys:

            out.write(
f"""\tif = {{
\t\tlimit = {{ var:bpm_{ministry}.interest_group ?= ig:ig_{ig} }}

"""
            )

            for institution in ministries[ministry]:

                short_name = institution.removeprefix("institution_")

                if short_name not in modifiers:
                    continue

                lawgroup = institution_lawgroup[institution]

                for modname, supported_igs in modifiers[short_name].items():

                    if modname == "" or "neutral" in modname:
                        continue

                    if ig not in supported_igs:
                        continue

                    out.write(
f"""\t\tactive_law:{lawgroup} = {{
\t\t\tadd_amendment = {{
\t\t\t\ttype = amendment_bpm_{institution.replace("institution_", "")}_{modname}_modifier
\t\t\t\tsponsor = prev.ig:ig_{ig}
\t\t\t}}
\t\t}}

"""
                    )

            out.write("\t}\n\n")

    out.write("}\n\n")

    # =========================================================
    # REMOVE AMENDMENTS
    # =========================================================

    out.write("bpm_remove_institution_amendments = {\n\n")

    for institution, lawgroup in institution_lawgroup.items():

        short_name = institution.removeprefix("institution_")

        if short_name not in modifiers:
            continue

        out.write(f"\t# {institution}\n\n")

        for modname in modifiers[short_name]:

            if modname == "":
                continue

            out.write(
f"""\tactive_law:{lawgroup} = {{
\t\trandom_scope_amendment = {{
\t\t\tlimit = {{
\t\t\t\ttype = amendment_type:amendment_bpm_{institution.replace("institution_", "")}_{modname}_modifier
\t\t\t}}
\t\t\tremove_amendment = yes
\t\t}}
\t}}

"""
            )

    out.write("}\n")

# -----------------------
# Load modifiers
# -----------------------

with open("support-scripts/cabinet/modifiers.json", encoding="utf8") as f:
    modifiers = json.load(f)

# -----------------------
# Output file (overwrite)
# -----------------------

with open("better-politics-mod/localization/english/bpm_cabgenamendments_l_english.yml", "w", encoding="utf-8-sig") as out:
    out.write("l_english:\n")
    for institution, modmap in modifiers.items():

        for modname in modmap.keys():

            if modname == "":
                continue

            inst_clean = institution.replace("institution_", "")

            key = f"amendment_bpm_{inst_clean}_{modname}_modifier"

            value = f"\"$bpm_cabinet_amendment$: $bpm_{inst_clean}_{modname}_modifier$\""

            out.write(f"\t{key}: {value}\n")