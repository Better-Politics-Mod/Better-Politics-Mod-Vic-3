import json
with open('./support-scripts/cabinet/institutions.json', 'r') as f:
    INSTITUTIONS = json.load(f)
    result = r"\n"
    
for inst in INSTITUTIONS:
    v = input(f"Value for {inst}>>")
    if v != "0":
        result += r"#v YYY%#! with [GetInstitutionType('institution_XXX').GetName]\n".replace('XXX', inst).replace('YYY', v)
print(result)