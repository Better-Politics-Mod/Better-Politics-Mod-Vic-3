import pdxpy, math


def generate(n, start):
    angle = 180 / n
    r = []
    for i in range(n+1):
        r.append((i*angle, start))
    return r

def generate_all(start, step, n):
    final_r = []
    #num_columns = len(n)
    for i in n:
        final_r.extend(generate(i, start))
        start -= step


    return sorted(final_r, key=lambda x: (x[0], x[1]))


XCENTER = 300
YCENTER = 200

def draw(r, color, xcenter=XCENTER, ycenter=YCENTER):
    result = []
    for i, v in enumerate(r):
        # calculate x y relative to 0, 0, where we have taken 500, 600 as the center of the circle
        angle  = v[0]
        radius = v[1]
        x = xcenter + radius * math.cos(angle * math.pi / 180)
        y = 1.5*ycenter - radius * math.sin(angle * math.pi / 180)
        result.append(
            {
                "icon": { 
                    "texture": f"gfx/interface/icons/{color}_circle.dds",
                    "size": r"{10 10}",
                    "visible": f"\"[And(GreaterThan_CFixedPoint(Country.MakeScope.Var('bpm_{color}_parl_max').GetValue, '(CFixedPoint){i}'), LessThan_CFixedPoint(Country.MakeScope.Var('bpm_{color}_parl_min').GetValue, '(CFixedPoint){i}'))]\"",
                    "position": r"{" + f"{int(x)} {int(y)}" + r"}"
                }
            }
        )
    return result


def creator(start=200, step=12, n=[50, 46, 43, 39, 36, 32, 29, 25], color="red"):
    last_r = generate_all(start, step, n)
    return draw(last_r, color)

 
#result = draw(generate(35), 176)

def make_parliament(color):


    res = str(pdxpy.PdxObject(creator(color=color)))

    # add 4 tabs before each line of res
    res = res.replace("\n", "\n" + "\t" * 2)

    fres = """
types politics_panel_types
{
    type bpm_parliament_visual_XXX = widget {
        size = { YYY ZZZ }
        using = tooltip_below
        GGG
        #using = entry_bg_fancy
    """.replace("XXX", color).replace('YYY', str(XCENTER*2)).replace('ZZZ', str(YCENTER*2)).replace("GGG", 
    f"visible = \"[And(Country.MakeScope.Var('bpm_{color}_parl_max').IsSet, Country.MakeScope.Var('bpm_{color}_parl_min').IsSet)]\"") + "\t" + res + """
    }
}
    """

    return fres

with open("output.txt", "w") as f:
    f.write(make_parliament("red"))
