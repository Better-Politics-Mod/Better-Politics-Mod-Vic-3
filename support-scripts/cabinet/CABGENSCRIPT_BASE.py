import json
with open('./support-scripts/cabinet/institutions.json', 'r') as f:
    INSTITUTIONS = json.load(f)

def gen_cabgenbase_cusfstr(insts):
    fstr = "#####This goes in bpm_CAB_interface.txt in customizable_localization/*#####\n\n"
    for inst in insts:
        fstr += """
text = {
    trigger = {
        owner.institution:institution_XXX.type ?= type
    }
    localization_key = bpm_minister_of_XXX
}
""".replace('XXX', inst)
    return fstr
        


def gen_cabgenbase_ult(insts):
    fstr = "#####This goes in bpm_CAB_values.txt in script_values/*#####\n\n"

    for inst in insts:
        fstr += """
    if = {
        limit = {
            var:bpm_minister_of_XXX ?= {
                bpm_is_antagonistic = yes
            }
        }
        add = 1
    }
""".replace('XXX', inst)
    fstr += "\nTotal institutions: " + str(len(insts))
    return fstr

with open('./support-scripts/cabinet/output_base.txt', 'w') as f:
    f.write('\n'.join([gen_cabgenbase_cusfstr(INSTITUTIONS), gen_cabgenbase_ult(INSTITUTIONS)]))
