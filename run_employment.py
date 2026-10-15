"""Employment breakdown and staffing-floor sensitivity (Sections 3.3 and 5.6).

Z3 (Eq. 15) is a sum over the six periods of the workforce needed in each period, so it
is measured in worker-periods. This script re-solves the baseline compromise and splits
Z3 by period into its two parts: workers needed for the tonnage handled
(tonnage / WC_t) and the staffing floor (e_min per operating facility). It then re-solves
the compromise with e_min = 10 and 40 (each on its own payoff bounds, since the
employment scale changes with e_min). Writes employment.json."""
import json
import pulp
import model as M

R = json.load(open("results.json"))
BND = {k: tuple(v) for k, v in R["bounds"].items()}


def breakdown(bnd, **kw):
    r = M.maxmin(bnd, **kw)
    floor = r["lam"] / 0.9 - 1e-7
    m, Z = M.build(**kw)
    T = {k: (Z[k] - bnd[k][0]) * (1.0 / (bnd[k][1] - bnd[k][0])) for k in Z}
    M.solve(m, pulp.lpSum(T.values()), extra=[T[k] >= floor for k in T])
    v = {x.name: x.value() for x in m.variables()}
    rows = []
    for t in range(M.T):
        ton = sum(v.get(f"x_{i}_{j}_{t}", 0) or 0 for i in M.I for j in range(len(M.CC)))
        nopen = sum(round(v.get(f"{p}_{i}_{t}", 0) or 0)
                    for p, n in (("aJ", len(M.CC)), ("aK", len(M.SC)), ("aL", 3), ("aM", 3)) for i in range(n))
        rows.append(dict(period=t + 1, tonnes=ton, wc=M.wc(t), tonnage_workers=ton / M.wc(t),
                         open=nopen, floor_workers=M.E_MIN * nopen,
                         total=ton / M.wc(t) + M.E_MIN * nopen))
    return M.val(Z), rows


base_v, base_rows = breakdown(BND)
out = dict(baseline=dict(Z=base_v, periods=base_rows), e_min_sweep=[])
orig = M.E_MIN
for e in (10.0, 25.0, 40.0):
    M.E_MIN = e
    pm = M.payoff()
    b = M.bounds_of(pm)
    v, rows = breakdown(b)
    out["e_min_sweep"].append(dict(e_min=e, Z=v, periods=rows,
                                   payoff_jobs=[pm[k]["Z3"] for k in ("Z1", "Z2", "Z3")]))
    print(f"e_min={e:.0f}: profit {v['Z1']/1e6:.2f} M SAR, util {v['Z2']:.2f}%, Z3 {v['Z3']:.0f} "
          f"worker-periods, avg {v['Z3']/6:.0f}/period", flush=True)
M.E_MIN = orig
out["solve_log"] = M.SOLVE_LOG
json.dump(out, open("employment.json", "w"), indent=1, default=float)
for r in base_rows:
    print(r)
