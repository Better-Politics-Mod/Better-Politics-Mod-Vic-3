mod = 'better-politics-mod/common/political_movements/' 
game = 'C:/Steam/steamapps/common/Victoria 3/game/common/political_movements/' 
import os
import re 
import pdxpy
r = re.compile(r'movement_(.*?) = \{')
def process_file(f):
    with open(f, 'r', encoding='utf-8') as file:
        data = file.read()
        matches = r.findall(data)
        return matches
    
def flatten(l):
    return [item for sublist in l for item in sublist]

def flatten_map(f, l):
    return flatten(list(map(f, l))) 

mod_files = [mod + file for file in os.listdir(mod)]
game_files = [game + file for file in os.listdir(game)]
result = list(set(list(flatten_map(process_file, mod_files)) + list(flatten_map(process_file, game_files))))


def create_setter(result):
    s = [] 
    n = False
    for k in result:
        if not n:
            s.append(
                pdxpy.PdxUtil.if_statement(
                    {"scope:polmov": [f"is_political_movement_type = movement_{k}"]},
                    pdxpy.PdxUtil.set_variable(f"bpm_movement_{k}_pressure", "scope:result")
                )
            )
        else:
            s.append(
                {"else_if": pdxpy.PdxUtil.if_statement(
                    {"scope:polmov": [f"is_political_movement_type = movement_{k}"]},
                    pdxpy.PdxUtil.set_variable(f"bpm_movement_{k}_pressure", "scope:result")
                )["if"]}
            )
        n = True
    return {"bpm_movement_setter": s}


def create_getter(result):
    s = [] 
    n = False
    for k in result:
        if not n:
            s.append(
                pdxpy.PdxUtil.if_statement(
                    {"scope:polmov": [f"is_political_movement_type = movement_{k}"]},
                    pdxpy.PdxUtil.set_variable(f"bpm_movement_pressure_getter_result", f"var:bpm_movement_{k}_pressure")
                )
            )
        else:
            s.append(
                {"else_if": pdxpy.PdxUtil.if_statement(
                    {"scope:polmov": [f"is_political_movement_type = movement_{k}"]},
                    pdxpy.PdxUtil.set_variable(f"bpm_movement_pressure_getter_result", f"var:bpm_movement_{k}_pressure")
                )["if"]}
            )
        n = True
    return {"bpm_movement_getter": s}


     

with open('support-scripts/movement_list.txt', 'w', encoding='utf-8') as file:
    file.write(str(pdxpy.PdxObject(create_setter(result))))
    file.write('\n')
    file.write(str(pdxpy.PdxObject(create_getter(result))))