INSTITUTIONS = ["schools", "police", , "colonial_affairs", "social_security", "workplace_safety", "health_system", "home_affairs", "centralization", "suffrage", "culture"]


def gen_cabgenbase_cusfstr(insts):
    fstr = ""
    for inst in insts:
        fstr += """
text = {
    trigger = {
        owner.institution:institution_XXX.type ?= type
    }
    localization_key = bpm_is_institution_XXX
}
""".replace('XXX', inst)
    return fstr
        

def gen_cabgenbase_addfstr(insts):
    fstr = ""
    for inst in insts:
        fstr += """
else_if = {
    limit = {
        type = owner.institution:institution_XXX.type
    }
    owner = { 
        if = {
            limit = {
                scope:addrem = yes
            }
            set_variable = {
                name = bpm_is_institution_XXX
                value = scope:actor
            }
        }
        else = {
            remove_variable = bpm_is_institution_XXX
        }
    }
}""".replace('XXX', inst)
    return fstr


def gen_cabgenbase_ult(insts):
    fstr = ""
    for inst in insts:
        fstr += """
    if = {
        limit = {
            var:bpm_is_institution_XXX ?= {
                bpm_is_antagonistic = yes
            }
        }
        add = 1
    }
""".replace('XXX', inst)
    return fstr
with open('output2.txt', 'w') as f:
    f.write('\n'.join([gen_cabgenbase_cusfstr(INSTITUTIONS), gen_cabgenbase_addfstr(INSTITUTIONS), gen_cabgenbase_ult(INSTITUTIONS)]))
