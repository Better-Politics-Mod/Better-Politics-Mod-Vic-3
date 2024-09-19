IGs = [
    'agrarian_populists', 'anarchists', 'conservatives', 'fascists', 'liberals', 'market_liberals', 
      'national_liberals', 'radicals', 'reactionaries', 'reformist_socialists', 'revolutionist_socialists', 
      'socialists', 'armed_forces', 'devout', 'industrialists', 'intelligentsia', 'landowners', 'petty_bourgeoisie', 'rural_folk', 'trade_unions'
]

txt = list(map(lambda x: x.strip().lower(), """
N/A
N/A
N/A
N/A
N/A
N/A
N/A
N/A
N/A
N/A
Subjugated_Security
Subjugated_Security
Security
Security
N/A
N/A
N/A
N/A
N/A
Subjugated_Security
""".split('\n')[1:-1]))

print(txt)

from pdxpy import PdxObject, PdxUtil

results = {}
for i, ig in enumerate(IGs):
    v = txt[i]
    results[ig] = v

t = "republic"
crisis = "crisis"

rr = f"bpm_update_sta_ideology_{crisis}_{t}"


p = []
for k, v in results.items():
    if v != "n/a":
        p.append(PdxUtil.if_statement([{"is_interest_group_type": "ig_" + k}], {"bpm_set_sta_ideology": {"ideology": v}}))


with open('./support-scripts/output.txt', 'w', encoding='utf-8') as f:
    f.write(str(PdxObject({rr: p})))

