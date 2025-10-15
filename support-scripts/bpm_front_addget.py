fronts = ["urban", "popular", "liberal", "republican", "labor", "socialist", "reactionary", "fascist", "nationalist", "peasant"]

# creates code that looks like
# bpm_add_ig_to_front = {
# 	bpm_remove_ig_from_all_fronts = yes
# 	if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_liberal
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_liberal_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_urban
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_urban_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_popular
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_popular_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_republican
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_republican_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_labor
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_labor_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_socialist
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_socialist_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_reactionary
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_reactionary_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_fascist
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_fascist_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_nationalist
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_nationalist_members
# 			target = scope:selected_ig
# 		}
# 	}
# 	else_if = {
# 		limit = {
# 			scope:selected_front_name = flag:bpm_front_peasant
# 		}
# 		add_to_variable_list = {
# 			name = bpm_front_peasant_members
# 			target = scope:selected_ig
# 		}
# 	}
# }

# from the list of fronts
def generator_add_ig(fronts):
    code = "bpm_add_ig_to_front = {\n"
    code += "\tbpm_remove_ig_from_all_fronts = yes\n"
    
    for front in fronts:
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tscope:selected_front_name = flag:bpm_front_{front}\n"
        code += f"\t\t}}\n"
        code += f"\t\tadd_to_variable_list = {{\n"
        code += f"\t\t\tname = bpm_front_{front}_members\n"
        code += f"\t\t\ttarget = scope:selected_ig\n"
        code += f"\t\t}}\n"
        code += "\t}\n"
    
    code += "}"
    return code

def generator_add_mov(fronts):
    code = "bpm_add_mov_to_front = {\n"
    code += "\tbpm_remove_mov_from_all_fronts = yes\n"
    
    for front in fronts:
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tscope:selected_front_name = flag:bpm_front_{front}\n"
        code += f"\t\t}}\n"
        code += f"\t\tadd_to_variable_list = {{\n"
        code += f"\t\t\tname = bpm_front_{front}_movs\n"
        code += f"\t\t\ttarget = scope:selected_mov\n"
        code += f"\t\t}}\n"
        code += "\t}\n"
    
    code += "}"
    return code

def generator_get_mov(fronts):
    code = "bpm_get_mov_front = {\n"
    
    for front in fronts:
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tis_target_in_variable_list ={{\n"
        code += f"\t\t\t\tname = bpm_front_{front}_movs\n"
        code += f"\t\t\t\ttarget = scope:selected_mov\n"
        code += f"\t\t\t}}\n"
        code += f"\t\t}}\n"
        code += f"\t\tflag:bpm_front_{front} = {{ save_scope_as = member_front_name }}\n"
        code += "\t}\n"
    
    code += "}"
    return code

def generator_get_ig(fronts):
    code = "bpm_get_ig_front = {\n"
    
    for front in fronts:
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tis_target_in_variable_list ={{\n"
        code += f"\t\t\t\tname = bpm_front_{front}_members\n"
        code += f"\t\t\t\ttarget = scope:selected_ig\n"
        code += f"\t\t\t}}\n"
        code += f"\t\t}}\n"
        code += f"\t\tflag:bpm_front_{front} = {{ save_scope_as = member_front_name }}\n"
        code += "\t}\n"
    
    code += "}"
    return code

def generator(fronts):
    return "\n\n".join([generator_add_ig(fronts), 
                 generator_add_mov(fronts), 
                 generator_get_mov(fronts), 
                 generator_get_ig(fronts),
                 generator_change_organization(fronts)])

#
# bpm_front_urban_organization = {
# 	if = {
# 		limit = {
# 			has_variable = bpm_front_urban_organization
# 		}
# 		value = var:bpm_front_urban_organization
# 	}
# 	else = {
# 		value = 0
# 	}
# }
# generate the above for each front
def generator_organization(fronts):
    code = ""
    
    for front in fronts:
        code += f"bpm_front_{front}_organization = {{\n"
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\thas_variable = bpm_front_{front}_organization\n"
        code += f"\t\t}}\n"
        code += f"\t\tvalue = var:bpm_front_{front}_organization\n"
        code += "\t}\n"
        code += "\telse = {\n"
        code += "\t\tvalue = 0\n"
        code += "\t}\n"
        code += "}\n\n"
    
    return code

#
# if = {
#     limit = {
#         scope:selected_front_name = flag:bpm_front_urban
#     }
#     change_variable = {
#         name = bpm_front_urban_organization
#         value = $v$
#     }
# }
# else_if = {
#     limit = {
#         scope:selected_front_name = flag:bpm_front_popular
#     }
#     change_variable = {
#         name = bpm_front_popular_organization
#         value = $v$
#     }
# }
# ...
# generator for the above
def generator_change_organization(fronts):
    code = "bpm_updated_front_organization = {\n"

    for front in fronts:
        code += f"\tif = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tscope:selected_front_name = flag:bpm_front_{front}\n"
        code += f"\t\t}}\n"
        code += f"\t\tchange_variable = {{\n"
        code += f"\t\t\tname = bpm_front_{front}_organization\n"
        code += f"\t\t\tvalue = $v$\n"
        code += f"\t\t}}\n"
        code += f"\t}}\n"
    
    code += "}\n"
    
    return code

# 
# bpm_movement_in_front = {
# 	trigger_if = {
# 		limit = {
# 			scope:member_front_name = flag:bpm_front_urban
# 		}
# 		is_target_in_variable_list = {
# 			name = bpm_front_urban_movs
# 			target = scope:selected_mov
# 		}
# 	}
# 	trigger_else_if = {
# 		limit = {
# 			scope:member_front_name = flag:bpm_front_popular
# 		}
# 		is_target_in_variable_list = {
# 			name = bpm_front_popular_movs
# 			target = scope:selected_mov
# 		}
# 	}
def generator_mov_in_front(fronts):
    code = "bpm_movement_in_front = {\n"
    
    for front in fronts:
        code += f"\ttrigger_if = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tscope:member_front_name = flag:bpm_front_{front}\n"
        code += f"\t\t}}\n"
        code += f"\t\tis_target_in_variable_list = {{\n"
        code += f"\t\t\tname = bpm_front_{front}_movs\n"
        code += f"\t\t\ttarget = scope:selected_mov\n"
        code += f"\t\t}}\n"
        code += "\t}\n"
    
    return code

def generator_ig_in_front(fronts):
    code = "bpm_ig_in_front = {\n"
    
    for front in fronts:
        code += f"\ttrigger_if = {{\n"
        code += f"\t\tlimit = {{\n"
        code += f"\t\t\tscope:member_front_name = flag:bpm_front_{front}\n"
        code += f"\t\t}}\n"
        code += f"\t\tis_target_in_variable_list = {{\n"
        code += f"\t\t\tname = bpm_front_{front}_members\n"
        code += f"\t\t\ttarget = scope:selected_ig\n"
        code += f"\t\t}}\n"
        code += "\t}\n"
    
    return code

def generator2(fronts):
    return "\n\n".join([generator_mov_in_front(fronts), 
                 generator_ig_in_front(fronts),
                 generator_organization(fronts)])


if __name__ == "__main__":
    with open("support-scripts/bpm_front_effects.txt", "w") as f:
        f.write(generator(fronts))
    with open("support-scripts/bpm_front_triggers.txt", "w") as f:
        f.write(generator2(fronts))