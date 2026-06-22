pats = """
bpm_revcell_XXX_lv1 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  state_bpm_revcell_progress_XXX_popscaled_add = 1
}

bpm_revcell_XXX_lv2 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  state_bpm_revcell_progress_XXX_popscaled_add = 3
}

bpm_revcell_XXX_lv3 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  state_bpm_revcell_progress_XXX_popscaled_add = 8
}
"""

patf = """
state_bpm_revcell_progress_XXX_popscaled_add = {
	decimals=0
	color=bad
	percent=no
	game_data={
		ai_value=0
	}
}
"""

patl = """

 bpm_revcell_XXX_lv1: "#crisis Small Revolutionary YYY Front#!"
 bpm_revcell_XXX_lv2: "Medium Revolutionary YYY Front"
 bpm_revcell_XXX_lv3: "Large Revolutionary YYY Front" 
 bpm_revcell_progress_XXX_popscaled_add: "YYY Front Revolution Progress (Population-Scaled)"

 bpm_revcell_progression_XXX: "#header Cell Progression#!\\nEach Month, the state invests a certain amount of [concept_bpm_state_capacity], based on its total [concept_bpm_state_capacity] and Laws. \
 If this is higher than the revolution progress, the cell will shrink, otherwise it will grow. \
 #bold Revolutionaries Progress#!: [State.MakeScope.ScriptValue('bpm_front_XXX_progressrate')|-v2] \
 \\n[State.MakeScope.GetScriptValueDesc('bpm_front_XXX_progressrate')]\\n \
 #bold Government Progress#!: [State.MakeScope.ScriptValue('bpm_state_repression')|-v2]\\n[State.MakeScope.GetScriptValueDesc('bpm_state_repression')]"

"""

fronts = ["urban", "popular", "liberal", "republican", "labor", "socialist", "reactionary", "fascist", "nationalist", "peasant"]

statmod = "better-politics-mod/common/static_modifiers/BPM_revolution_cells.txt"
funcmod = "better-politics-mod/common/modifier_type_definitions/bpm_revolution_cell_modifiers.txt"
lmod = "out.yml"

st = ""
ft = ""
lt = ""
for front in fronts:
    st+=pats.replace("XXX", front)
    ft+=patf.replace("XXX", front)
    lt+=patl.replace("XXX", front).replace("YYY", front.capitalize())

with open(statmod, "w") as f:
    f.write(st)

with open(funcmod, "w") as f:
    f.write(ft)

with open(lmod, "w") as f:
    f.write(lt)