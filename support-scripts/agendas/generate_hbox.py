def main():
    final_text = """
hbox = {
"""
    with open('support-scripts/agendas/data.pairs', 'r') as f:
        pairs = f.readlines()  
    pairs_dict = {}
    for pair in pairs:
        pair = pair.strip().split(':')
        pairs_dict[pair[0]] = pair[1]

    with open('support-scripts/agendas/config.cfg', 'r') as f:
        config_raw = f.readlines()
    config = {}
    for line in config_raw:
        line = line.strip().split('=')
        if '"' in line[1]:
            config[line[0]] = line[1].replace('"', '')
        else:
            config[line[0]] = int(line[1])

    for i in range(1, config["slots"]+1):
        final_text += generate_text_for_slot(pairs_dict.items(), config, str(i), i != config["slots"])
    
    final_text += "\n}"

    with open('support-scripts/agendas/output.txt','w') as f:
        f.write(final_text)


def generate_text_for_slot(pairs, config, slot, v):
    text = """
    # Agenda slot XXX

    widget = {
        size = { 27 32 }
        visible = "[InterestGroup.MakeScope.Var('bpm_agendas_ig_agenda_slot_XXX').IsSet]"
        tooltip = "bpm_IGA_slotXXX_localize"
""".replace('XXX', slot)
    for pair in pairs:
        text += """
        icon = {
            texture = "gfx/interface/icons/agenda_icons/ZZZ.dds"
            visible = "[EqualTo_CFixedPoint(InterestGroup.MakeScope.Var('bpm_agendas_ig_agenda_slot_XXX').GetValue, '(CFixedPoint)YYY')]"
            using = tooltip_above
            size = { 27 27 }
        }
""".replace('XXX', slot).replace('YYY', pair[0]).replace('ZZZ', pair[1])
    text += "    }"
    if v:
        text += """
    expand = {}
"""
    return text

if __name__ == '__main__':
    main()