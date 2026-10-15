"""Stage 2 compromise (baseline payoff bounds, two phases) on the sites chosen by the
joint maximum-profit model (joint.json). Writes joint_sites.json."""
import json
import model as M
J = json.load(open("joint.json")); R = json.load(open("results.json"))
BND = {k: tuple(v) for k, v in R["bounds"].items()}
M.CC[:] = [M.CITIES.index(c) for c in J["maxprofit"]["cc"]]
M.SC[:] = [M.CITIES.index(c) for c in J["maxprofit"]["sc"]]
r = M.maxmin(BND)
pm = M.payoff()
m, Z = M.build(); M.solve(m, Z["Z1"]); V = m.variablesDict()
sc_used = [M.CITIES[M.SC[k]] for k in range(len(M.SC)) if any(V[f"aK_{k}_{t}"].value() > .5 for t in range(M.T))]
out = dict(cc=J["maxprofit"]["cc"], sc=J["maxprofit"]["sc"],
           compromise={k: r[k] for k in ("Z1", "Z2", "Z3", "lam")},
           maxprofit=pm["Z1"]["Z1"], sc_used_maxprofit=sc_used, solve_log=M.SOLVE_LOG)
json.dump(out, open("joint_sites.json", "w"), indent=1, default=float)
print(out["compromise"], out["maxprofit"])
