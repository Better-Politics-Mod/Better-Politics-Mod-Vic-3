# We have INJECT at home
import regex
import pathlib
import json

with open("diplo_plays_inject.json", 'r') as file:
    input = json.load(file)

with open ( f"{pathlib.Path.home()}/.local/share/Steam/steamapps/common/Victoria 3/game/common/diplomatic_plays/00_diplomatic_plays.txt", "r") as f:
    content = f.read()

with open("../better-politics-mod/common/diplomatic_plays/zz_bpm_diploplay_override.txt", "w+",encoding="utf-8-sig") as f:
    for dp, condition in input.items():
        match = regex.search(fr'{dp} =\s*(\{{(?:[^{{}}]++|(?1))*\}})',content).group()
        if condition['exeption'] == True:
            match = match.replace(
                "aggressive_diplomatic_plays_permitted = yes",
                str("aggressive_diplomatic_plays_permitted = yes\n")+str(f"\t\tOR = {{ \n\t\t\tbpm_aggressive_diplomacy_permitted = yes \n\t\t\t{dp.replace('dp','bpm_exception')}_permitted = yes \n\t\t}}")
            )
        else:
            match = match.replace(
                "aggressive_diplomatic_plays_permitted = yes",
                str("aggressive_diplomatic_plays_permitted = yes\n")+str(f"\t\tbpm_aggressive_diplomacy_permitted = yes")
            )
        f.write(str("REPLACE:")+str(match))
        f.write('\n\n')

        



