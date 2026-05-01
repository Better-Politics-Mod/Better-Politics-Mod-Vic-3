import regex
import pathlib

regions = {}
randomized_chars = []
role_politician = []

with open('../chars_to_edit.txt', 'r') as f:
    to_edit = f.read()
    chars = regex.findall(r'^[a-zA-Z].*(?= =)',to_edit,flags=regex.MULTILINE)
    for char in chars:
        template = regex.compile(fr'{char} =\s*(\{{(?:[^{{}}]++|(?1))*\}})')
        match = regex.search(template,to_edit).group()
        if match:
            try:
                region = regex.search("home_region.*",match).group()
                if region:
                    regions[char]=region
            except:
                pass
            if "chance =" in match:
                randomized_chars.append(char)
            if "role = character_role_politician" in match:
                role_politician.append(char)

for file in pathlib.Path('.').glob('*.txt'):
    with open(file, 'r') as f:
        current_file = f.read()
    for char in chars:
        template = regex.compile(fr'REPLACE:{char} =\s*(\{{(?:[^{{}}]++|(?1))*\}})')
        if char in regions:
            match = regex.search(template,current_file)
            if match:
                replacement = match.group()
                if not 'home_region =' in replacement:
                    if "traits = {" in replacement:
                        replacement = replacement.replace("traits = {",f"{regions[char]}\n\ttraits = {{")
                    elif "trait_generation" in replacement:
                        replacement = replacement.replace("trait_generation = {",f"{regions[char]}\n\trait_generation = {{")
                if not char in randomized_chars:
                    replacement = regex.sub(r'chance =.*','#guaranteed to spawn if possible',replacement)
                    #print(replacement)
                if char in role_politician:
                    replacement = replacement.replace('ig_leader = yes','role = character_role_politician')
                current_file = current_file.replace(match.group(),replacement)
    with open(file, 'w', encoding ="utf-8") as f:
        f.write(current_file)