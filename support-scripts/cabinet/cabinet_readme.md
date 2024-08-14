# How to setup an already registered institution

- Go to scripted_triggers/bpm_CAB_triggers and modify bpm_is_antagonistic and bpm_is_antagonistic_hypothetical by following the Cabinet modifiers table available in the google docs (https://docs.google.com/document/d/1HWZgEZsPGhpzg-vzSsyvWd0yzwPtwjh2EX8vWRFerDs/edit?usp=sharing).

- Select a row to add in the modifiers table and add the static modifiers in static_modifiers/BPM_CAB_modifiers
    - The Modifiers **MUST** be called bpm_{INSTITUTION}_{ANY NAME}_modifier (ex. bpm_schools_liberals_modifier)
    - The Modifier can be the same for multiple IGs (ex. bpm_schools_liberals_modifier for libs, marlibs and natlibs)
    - Modifiers that are for INGs should have +1 rigidity and modifiers for IDG -1 rigidity.
    - If the table says NTRL, create a modifier with either +1 rigidity for INGs and -1 rigidity for IDGs and nothing else. (Maybe call it neutralidg or neutraling for consistency?)
    - Add a modifier named bpm_{INSTITUTION}_attraction_modifier

- Run py support-scripts/cabinet/cabgenscript.py, this will modify the file support-scripts/cabinet/output.txt
    - When the script asks for the name of the institution it should be its code name, like social_security of schools
    - Then, pick the appropriate modifier for each IG as indicated, picking the neutral one for NTRL IGs and simply skipping with enter with ANTAG IGs
    - The first two parts of the output should be added directly to scripted_effects/BPM_CAB_MODIFIERS_effects.txt (that is bpm_remove_institution_modifiers_{INSTITUTION} and bpm_reload_institution_modifiers_{INSTITUTION} )
    - The bpm_reload_institution_modifiers effect should be edited to add the removal of the attraction modifier and to call bpm_reload_institution_modifiers_{INSTITUTION}
    - The third part should be added directly to customizable_localization/bpm_CAB_interface
    - The last two parts should be added directly to localization/english/BPM_cab_modifiers_l_english

Done!

