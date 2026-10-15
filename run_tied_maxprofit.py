"""Maximum profit of every tied Stage 1 segregation siting (Section 5.4).

equity_lp.py compares the 430 equal-cost segregation sitings under the fixed operating
schedule of the baseline compromise. Here the schedule is free: for each siting, with the
Phase 1 collection centres kept, Stage 2 is solved for maximum profit. This isolates the
cost of the Phase 2 distance tie-break, which chooses among the sitings without looking at
Stage 2. Writes tied_maxprofit.json."""
import json
import model as M
import equity_lp as EQ
base = list(M.SC); rows = []
for c in EQ.CONFIGS:
    M.SC[:] = list(c)
    m, Z = M.build()
    try:
        M.solve(m, Z["Z1"])
        V = m.variablesDict()
        used = [M.CITIES[c[k]] for k in range(3) if any(V[f"aK_{k}_{t}"].value() > .5 for t in range(M.T))]
        rows.append(dict(sites=[M.CITIES[k] for k in c], Z1=M.val(Z)["Z1"], used=used,
                         stage1=sorted(c) == sorted(base)))
    except M.NotSolved as e:
        rows.append(dict(sites=[M.CITIES[k] for k in c], feasible=False, status=str(e)))
M.SC[:] = base
ok = [r for r in rows if "Z1" in r]
best = max(ok, key=lambda r: r["Z1"]); s1 = next(r for r in ok if r["stage1"])
out = dict(n=len(rows), n_feasible=len(ok), best=best, stage1=s1,
           n_within_01pct=sum(r["Z1"] >= 0.999 * best["Z1"] for r in ok),
           min=min(r["Z1"] for r in ok), rows=rows, solve_log=M.SOLVE_LOG)
json.dump(out, open("tied_maxprofit.json", "w"), indent=1, default=float)
print(len(ok), best, s1, out["n_within_01pct"], out["min"])
