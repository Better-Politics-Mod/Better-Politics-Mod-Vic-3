mod = 'better-politics-mod/common/political_movements/' 
game = 'C:/Steam/steamapps/common/Victoria 3/game/common/political_movements/' 
import os
import re 
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

print(result)