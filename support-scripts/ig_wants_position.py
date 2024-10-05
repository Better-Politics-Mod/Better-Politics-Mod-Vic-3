import pandas as pd
import pdxpy

# Read IGWANTSPOSITIONDATA.csv as pandas
# The first row is the header, and the first column is the index
df = pd.read_csv('support-scripts/IGWANTSPOSITIONDATA.csv', header=0, index_col=0)

# Iterate over the columns and rows
result = [
    {"value": 5}
]
for column in df.columns:
    rsub = [
        {"owner.institution:institution_" + column + ".type": "scope:bpm_reference_institution_type"}
    ]
    sub = []
    for index in df.index:
        # Print the column (header), index, and value
        if df.at[index, column] == 'x':     
            sub.append({"is_interest_group_type": 'ig_' + index})
        #print(f"Header: {column}, Index: {index}, Value: {df.at[index, column]}")
    if len(sub) > 0:
        result.append(
            pdxpy.PdxUtil.if_statement(
                rsub + [{'OR': sub}],
                [{"subtract": {"value": 3, "desc": "bpm_ig_wants_position"}}],
            )
        )

with open('support-scripts/ig_wants_position.txt', 'w') as f:
    f.write(str(pdxpy.PdxObject({'bpm_cost_ig_position': result})))


# we want to create a 