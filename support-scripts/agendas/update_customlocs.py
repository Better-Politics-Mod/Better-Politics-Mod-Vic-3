def main():
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

    final_text = ""
    for i in range(1, config["slots"]+1):
        final_text += generate_text_for_slot(pairs_dict.items(), config, str(i))

    with open(config['target'], 'w') as f:
        f.write(final_text)



def generate_text_for_slot(pairs, config, slot):
    text = """
bpm_IGA_custom_localization_for_slot_XXX = {
    type = interest_group
	random_valid = no
""".replace('XXX', slot)
    for pair in pairs:
        text += """
    text = {
        trigger = {
            var:bpm_agendas_ig_agenda_slot_XXX = YYY
        }
        localization_key = ZZZ
    }
""".replace('XXX', slot).replace('YYY', pair[0]).replace('ZZZ', pair[1])
    text += """
    text = {
        trigger = {
            always = no
        }
        fallback = yes
        localization_key = XXX
    }
}
""".replace('XXX', config['default'])
    return text


if __name__ == '__main__':
    main()