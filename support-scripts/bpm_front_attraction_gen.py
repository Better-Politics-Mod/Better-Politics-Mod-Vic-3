import pandas


# read front_data.csv
def read_front_data():
    df = pandas.read_csv("support-scripts/front_data.csv")
    return df

# map over each row
def map_over_rows(df):
    print("Mapping over rows")
    t = []
    t2 = []
    for index, row in df.iterrows():
        row = row.dropna()
        title = row[0].lower()
        # convert the rest to pairs (key, value)
        rest = row[1:].to_dict()
        ismov = False
        if list(rest.values())[0].isnumeric():
            ismov = True
        base_text = """
# XXX
bpm_front_attraction_dispatch_XXX = {
	scope:selected_WWW = {
""".replace("XXX", title).replace("WWW", 'ig' if not ismov else 'mov')
        isif = True
        for key, value in rest.items():
            base_text += handle_pair(key, value, isif)
            isif = False

        base_text += """
        else = {
            value = 0
        }
    }
}
"""
        t.append(base_text)

    with open("support-scripts/bpm_front_attraction_dispatch.txt", "w") as f:
        f.write("\n".join(t))

def handle_pair(key, value, isif=False):
    return """
        ZZZ = {
			limit = {
				prev = flag:bpm_front_XXX
			}
			value = bpm_front_attraction_YYY
			multiply = bpm_front_XXX_multiplier
		}
""".replace("XXX", key.lower()).replace("YYY", value.lower()).replace("ZZZ", "if" if isif else "else_if")




if __name__ == "__main__":
    # read front_data.csv
    df = read_front_data()
    # map over each row
    map_over_rows(df)