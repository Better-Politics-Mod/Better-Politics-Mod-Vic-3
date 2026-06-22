import pandas

# read front_data.csv
def read_front_data():
    df = pandas.read_csv("support-scripts/front_data.csv", index_col=0)
    return df

# map over each column (front)
def map_over_rows(df):
    t = []
    
    # Iterate over columns (fronts)
    for front in df.columns:
        base_text = """
bpm_front_attraction_dispatch_WWW_mov = {
    type = political_movement
""".replace("WWW", front.lower())
        
        isif = True
        
        # Iterate over rows (interest group types) in this column
        for ig_type, value in df[front].items():
            if pandas.isna(value):
                continue
            
            # check if value is a digit
            if not str(value).isnumeric():
                print(str(value))
                continue 
            
            base_text += handle_pair(ig_type, value, isif)
            isif = False
        
        base_text += """
    text = {
        trigger = {
            always = no
        }
        fallback = yes
        localization_key = bpm_unknown_grid
    }
}
"""
        t.append(base_text)
    
    with open("better-politics-mod/common/customizable_localization/bpm_front_ttgenmov.txt", "w") as f:
        f.write("\n".join(t))

def handle_pair(key, value, isif=False):
    return """
    text = {
        trigger = {
            is_political_movement_type = movement_XXX
        }
        localization_key = bpm_front_data_YYY_tt
    }
""".replace("XXX", key.lower()).replace("YYY", value.lower())

if __name__ == "__main__":
    # read front_data.csv
    df = read_front_data()
    # map over each column (front)
    map_over_rows(df)