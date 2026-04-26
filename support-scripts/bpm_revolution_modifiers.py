pats = """
bpm_revcell_XXX_lv1 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  bpm_revcell_progress_XXX_popscaled_add = 1
}

bpm_revcell_XXX_lv2 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  bpm_revcell_progress_XXX_popscaled_add = 2
}

bpm_revcell_XXX_lv3 = {
  icon = "gfx/interface/icons/front_icons/XXX_front.dds"
  bpm_revcell_progress_XXX_popscaled_add = 3
}
"""

patf = """
bpm_revcell_progress_XXX_popscaled_add = {
	decimals=0
	color=bad
	percent=no
	game_data={
		ai_value=0
	}
}
"""

fronts = ["urban", "popular", "liberal", "republican", "labor", "socialist", "reactionary", "fascist", "nationalist", "peasant"]

statmod = "better-politics-mod/common/static_modifiers/BPM_revolution_cells.txt"
funcmod = "better-politics-mod/common/modifier_type_definitions/bpm_revolution_cell_modifiers.txt"


st = ""
ft = ""
for front in fronts:
    st+=pats.replace("XXX", front)
    ft+=patf.replace("XXX", front)

with open(statmod, "w") as f:
    f.write(st)

with open(funcmod, "w") as f:
    f.write(ft)
