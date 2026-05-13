fronts = [
    "urban", "popular", "liberal", "republican", "labor",
    "socialist", "reactionary", "fascist", "nationalist", "peasant"
]

tt = """

	dynamic_country_name = {
		name = dyn_c_revolutionary_YYY_tag
		adjective = ATL_ADJ
		priority = 1
		trigger = {
			scope:actor ?= { var:bpm_country_revolutionary_front = flag:bpm_front_YYY }
		}
	}
"""

rest = ""
for f in fronts:
	rest += tt.replace("YYY", f)

t = """
DXXX = {
	VVV
}
""".replace("VVV", rest)
res = ""
for i in range(0, 100):
    res += t.replace("XXX", str("{:02d}".format(i)))

with open("support-scripts/bpmgendyn.txt", "w") as f:
    f.write(res)