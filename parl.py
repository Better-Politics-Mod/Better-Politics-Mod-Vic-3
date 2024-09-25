import pdxpy, math


def generate(n):
    angle = 180 / n
    r = []
    for i in range(n+1):
        r.append(i*angle)
    return r

def draw(r, radius):
    result = []
    for v in r:
        # calculate x y relative to 0, 0, where we have taken 500, 600 as the center of the circle
        x = 500 + radius * math.cos(v * math.pi / 180)
        y = 600 - radius * math.sin(v * math.pi / 180)
        result.append(
            {
                "icon": { 
                    "texture": "gfx/interface/icons/red_circle.dds",
                    "size": r"{10 10}",
                    "position": r"{" + f"{int(x)} {int(y)}" + r"}"
                }
            }
        )
    return result


start = 200 
step = 12
n = [50, 46, 43, 39, 36, 32, 29]

final_result = []

for i in n:
    final_result.extend(draw(generate(i), start))
    start -= step

#result = draw(generate(35), 176)

res = str(pdxpy.PdxObject(final_result))

# add 4 tabs before each line of res
res = res.replace("\n", "\n" + "\t" * 4)

with open("output.txt", "w") as f:
    f.write(res)
