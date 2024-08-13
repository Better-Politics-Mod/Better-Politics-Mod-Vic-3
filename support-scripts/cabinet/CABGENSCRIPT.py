import re
import json

IGs = [
    'agrarian_populists', 'anarchists', 'conservatives', 'fascists', 'liberals', 'market_liberals', 
      'national_liberals', 'radicals', 'reactionaries', 'reformist_socialists', 'revolutionist_socialists', 
      'socialists', 'armed_forces', 'devout', 'industrialists', 'intelligentsia', 'landowners', 'petty_bourgeoisie', 'rural_folk', 'trade_unions'
]

def get_data():
    with open('better-politics-mod/common/static_modifiers/BPM_CAB_modifiers.txt', 'r', encoding='utf-8') as f:
        t = f.read()

    modifying_institution_name = input("Modifying institution>> ")

    pat = re.compile(f"bpm_{modifying_institution_name}_(.*?)_modifier")

    modifiers = pat.findall(t)
    dynamic_modifiers = list(filter(lambda x: x not in ['fallback', 'attraction'], modifiers))

    igtomod = {}
    
    with open('./support-scripts/cabinet/modifiers.json', 'r', encoding='utf-8') as f:
        allmodtoig = json.load(f)

    if allmodtoig.get(modifying_institution_name, None) is not None:
        modtoig = allmodtoig[modifying_institution_name]
        return modtoig, dynamic_modifiers, modifying_institution_name, modifiers

    for ig in IGs:
        print(f"Which modifier out of: {dynamic_modifiers} should be used for {ig}?")
        mod = input(f"{ig}>> ")
        igtomod[ig] = mod


    # convert igtomod to modtoig
    modtoig = {}
    for ig, mod in igtomod.items():
        if mod not in modtoig:
            modtoig[mod] = [ig]
        else:
            modtoig[mod].append(ig)

    #modtoig = {'agpops': ['agrarian_populists', 'anarchists', 'conservatives', 'fascists', 'liberals', 'market liberals', 'national liberals', 'radicals', 'reactionaries', 'reformist socialists', 'revolutionist socialists', 'socialists', 'armed forces', 'devout', 'industrialists', 'intelligentsia', 'landowners', 'petty bourgeoisie', 'rural folk', 'trade unions']}

    return modtoig, dynamic_modifiers, modifying_institution_name, modifiers

def main():
    modtoig, dynamic_modifiers, nm, mods = get_data()


    remove_modifiers = map(lambda x: f"remove_modifier = bpm_{nm}_{x}_modifier", dynamic_modifiers)
    remove_fstr = f"bpm_remove_institution_modifiers_{nm}" + " = {\n" + '\n'.join(map(lambda x: f"   {x}", remove_modifiers)) + "\n}\n"
    giga_fstr = '\n'.join(map(lambda x: f"bpm_{nm}_{x}_modifier:0 \"Minister of Colonial Affairs\"", dynamic_modifiers))
    add_fstr = gen_add_fstr(modtoig, dynamic_modifiers, nm)
    locs_fstr = gen_locs_fstr(nm, mods)
    custlocs_fstr = gen_custlocs_fstr(nm, mods, modtoig)

    with open('./support-scripts/cabinet/output.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join([remove_fstr, add_fstr, locs_fstr, custlocs_fstr, giga_fstr]))
    with open('./support-scripts/cabinet/modifiers.json', 'r', encoding='utf-8') as f:
        allmodtoig = json.load(f)
    allmodtoig[nm] = modtoig
    with open('./support-scripts/cabinet/modifiers.json', 'w', encoding='utf-8') as f:
        json.dump(allmodtoig, f, indent=4)

def gen_locs_fstr(nm, dynamic_modifiers):
    return '\n'.join(map(lambda x: f"bpm_{nm}_{x}_modifier_desc: \"[GetStaticModifier('bpm_{nm}_{x}_modifier').GetDesc]\"", dynamic_modifiers))


def gen_custlocs_fstr(nm, dynamic_modifiers, modtoig):
    custlocs_fstr = ""
    for mod in dynamic_modifiers:
        if modtoig.get(mod, None) is None:
            continue
        custlocs_fstr += """
text = {
    trigger = {
        interest_group = {
            OR = {
"""
        for ig in modtoig.get(mod, []):
            custlocs_fstr += f"                     is_interest_group_type = ig_{ig}\n"
        custlocs_fstr += "              }\n"
        custlocs_fstr += "           }\n"
        custlocs_fstr += "        }\n"
        custlocs_fstr += f"        localization_key = bpm_{nm}_{mod}_modifier_desc\n"
        custlocs_fstr += "}\n"
    return custlocs_fstr

def gen_add_fstr(modtoig, dynamic_modifiers, nm):
    add_fstr = """
bpm_reload_institution_modifiers_XXX = {
    institution:institution_XXX = {
        bpm_remove_institution_modifiers_XXX = yes
    }
    if = {
        limit = {
            var:bpm_is_institution_XXX ?= {
                OR = {
                    is_character_alive = no
                    NOT = { exists = interest_group } 
                }
            }
        }
        remove_variable = bpm_is_institution_XXX
    }
    if = {
        limit = {
            has_variable = bpm_is_institution_XXX
        }
        var:bpm_is_institution_XXX.interest_group = {
""".replace('XXX', nm)
    for mod, igs in modtoig.items():
        if mod == "": continue
        if len(igs) == 1:
            add_fstr += "           bpm_reload_modifier_inst_singlet = {"
            add_fstr +=f"""
                IG1 = {igs[0]}
                INST = {nm}
                MOD = bpm_{nm}_{mod}_modifier
"""
        if len(igs) == 2:
            add_fstr += "           bpm_reload_modifier_inst_doublet = {"
            add_fstr +=f"""
                IG1 = {igs[0]}
                IG2 = {igs[1]}
                INST = {nm}
                MOD = bpm_{nm}_{mod}_modifier
"""
        if len(igs) == 3:
            add_fstr += "           bpm_reload_modifier_inst_triplet = {"
            add_fstr +=f"""
                IG1 = {igs[0]}
                IG2 = {igs[1]}
                IG3 = {igs[2]}
                INST = {nm}
                MOD = bpm_{nm}_{mod}_modifier
"""
        add_fstr += '           }\n'

    add_fstr += """
            add_modifier = {
                name = bpm_XXX_attraction_modifier
                multiplier = institution:institution_XXX.investment
            }
        }
""".replace('XXX', nm)
    add_fstr += """    }
}
"""
    return add_fstr

if __name__ == '__main__':
    main()