fronts = [
    "urban", "popular", "liberal", "republican", "labor",
    "socialist", "reactionary", "fascist", "nationalist", "peasant"
]

progressrate_template = """bpm_front_{f}_progressrate = {{
    value = 0
    owner = {{
        add = {{
            value = 0
            every_in_list = {{
                variable = bpm_front_{f}_members
                add = {{
                    value = bpm_ig_organization_val
                    multiply = ig_clout
                    multiply = 100
                }}
            }}
            desc = "bpm_front_progress_from_ig"
        }}
        add = {{
            value = 0
            every_in_list = {{
                variable = bpm_front_{f}_movs
                add = {{
                    value = political_movement_support
                    multiply = political_movement_radicalism
                    multiply = 100
                }}
            }}
            desc = "bpm_front_progress_from_movs"
        }}
    }}
    multiply = turmoil
}}
"""

progressvalue_template = """bpm_front_{f}_progress_value = {{
    value = 0
    every_scope_state = {{
        limit = {{
            has_variable = bpm_revcell_{f}
        }}
        add = {{
            value = modifier:state_bpm_revcell_progress_{f}_popscaled_add
            multiply = {{
                value = state_population
                divide = owner.total_population
            }}
        }}
    }}
}}
"""

with open("bpm_fronts.txt", "w") as out:
    for f in fronts:
        out.write(progressrate_template.format(f=f))
        out.write("\n")

    out.write("\n")

    for f in fronts:
        out.write(progressvalue_template.format(f=f))
        out.write("\n")