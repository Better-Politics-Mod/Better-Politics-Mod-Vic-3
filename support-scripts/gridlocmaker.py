INSTITUTIONS = ["colonial_affairs", "social_security", "workplace_safety", "schools", "police", "health_system", "home_affairs", "centralization", "suffrage", "culture"]
result = r"\n"
for inst in INSTITUTIONS:
    v = input(f"Value for {inst}>>")
    if v != "0":
        result += r"#v YYY%#! with [GetInstitutionType('institution_XXX').GetName]\n".replace('XXX', inst).replace('YYY', v)
print(result)