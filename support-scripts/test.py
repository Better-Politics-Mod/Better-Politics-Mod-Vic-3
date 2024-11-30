with open("support-scripts/patient12.txt", "r") as f:
    s_lines = f.readlines()

f_lines = []
enterCounter = 0
counting = False
saved_lines = []
for line in s_lines:

    if counting:
        if "{" in line:
            enterCounter += 1
        if "}" in line:
            enterCounter -= 1
            if enterCounter == 0:
                counting = False
        if enterCounter > 0:
            saved_lines.append(line)

    if "interest_group_leader_trigger" in line and "non_interest_group_leader_trigger" not in line:
        counting = True
        enterCounter += 1
    if "non_interest_group_leader_trigger" in line:
        f_lines.append(line)
        f_lines.append("        interest_group = {\n")
        f_lines.extend(map(lambda x: "    " + x, saved_lines))
        f_lines.append("    	}\n")
        saved_lines = []
    else:
        f_lines.append(line)
                

with open("support-scripts/patient13.txt", "w") as f:
    f.writelines(f_lines)