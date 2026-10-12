import json,sys
p=json.load(open(sys.argv[1])); g={}
ng=p["nigeria"]
g["official_usd_present"]=ng["USD"]["official_selling_rate"] is not None and ng["USD"]["official_rate_date"] is not None
g["official_gbp_eur_present"]=all(ng[c]["official_selling_rate"] is not None for c in("GBP","EUR"))
def prem_ok(d):
    if d["parallel_buy_low"] is None: return True
    m=(d["parallel_buy_low"]+d["parallel_buy_high"])/2
    return abs(round((m/d["official_selling_rate"]-1)*100,2)-d["premium_pct"])<=0.01
g["premium_recomputes"]=all(prem_ok(ng[c]) for c in ng) if g["official_usd_present"] else False
g["markets_complete"]=all(m["asof"] and all(v is not None for v in m["rates"].values()) for m in p["markets"].values())
g["no_provider_names"]=not any(n in json.dumps(p).lower() for n in("abokiforex","ngnrates","nairarates"))
g["early_look_labelled"]="previous close" in p.get("label","").lower()
g["no_exception_state"]=p.get("exception_state") in (None,"")
for k,v in g.items(): print(("PASS" if v else "FAIL"),k)
sys.exit(0 if all(g.values()) else 1)
