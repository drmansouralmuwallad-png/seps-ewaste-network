"""Why a stricter recovery mandate raises profit (Section 5.5).

Part A decomposes profit at the 70, 80 and 90% mandates into recycling revenue,
refurbishing revenue, transport cost and fixed operating cost, both for the maximum-profit
design and for the two-phase compromise on the baseline payoff bounds, and records the
tonnage sent to each outlet.
Part B adds what the baseline omits, a per-tonne processing cost at recycling and
refurbishing centres and a sold yield below one, and reports the maximum-profit change
from 70% to 90% on a grid, with the break-even processing cost at each yield.
Writes recovery.json."""
import json
import pulp
import model as M

R = json.load(open("results.json")); BND = {k: tuple(v) for k, v in R["bounds"].items()}
DELTA = 0.10
MANDATES = [("70", 0.25, 0.45), ("80", 0.30, 0.50), ("90", 0.35, 0.55)]


def parts(m, Z):
    v = {k: pulp.value(e) for k, e in m._parts.items()}
    V = m.variablesDict()
    ton = lambda pre: sum(V[n].value() for n in V if n.startswith(pre))
    v.update(Z1=pulp.value(Z["Z1"]), Z2=pulp.value(Z["Z2"]), Z3=pulp.value(Z["Z3"]),
             t_rec=ton("r_"), t_ref=ton("f_"), t_disp=ton("d_"),
             slots=sum(V[n].value() > .5 for n in V if n[:3] in ("aJ_", "aK_", "aL_", "aM_")))
    return v


def maxprofit(p):
    m, Z = M.build(p=p); M.solve(m, Z["Z1"]); return parts(m, Z)


def compromise(p):
    T = lambda Z, k: (Z[k] - BND[k][0]) * (1.0 / (BND[k][1] - BND[k][0]))
    m, Z = M.build(p=p)
    lam = pulp.LpVariable("lam", lowBound=0, upBound=1)
    M.solve(m, lam, extra=[T(Z, k) >= lam * (1.0 / (1 - DELTA)) for k in ("Z1", "Z2", "Z3")])
    v1 = M.val(Z)
    lam1 = (1 - DELTA) * min((v1[k] - BND[k][0]) / (BND[k][1] - BND[k][0]) for k in v1)
    m, Z = M.build(p=p)
    M.solve(m, pulp.lpSum(T(Z, k) for k in ("Z1", "Z2", "Z3")),
            extra=[T(Z, k) >= lam1 / (1 - DELTA) - 1e-7 for k in ("Z1", "Z2", "Z3")])
    out = parts(m, Z); out["lam"] = lam1
    return out


if __name__ == "__main__":
    out = dict(prices=dict(pr=M.PR, pref=M.PL * M.SHARE_LOCAL + M.PI * (1 - M.SHARE_LOCAL)),
               total_tonnes=float(M.EWASTE.sum()))
    out["A"] = {}
    for name, a, b in MANDATES:
        p = {"alpha": a, "beta": b}
        out["A"][name] = dict(alpha=a, beta=b, maxprofit=maxprofit(p), compromise=compromise(p))
        print(name, {k: round(v) for k, v in out["A"][name]["maxprofit"].items()}, flush=True)
        print(name, {k: round(v, 3) for k, v in out["A"][name]["compromise"].items()}, flush=True)
    grid = []
    for y in (1.0, 0.8, 0.6):
        for c in (0, 200, 400, 600, 800, 1000, 1200):
            row = dict(yield_=y, cost=c)
            for name, a, b in (MANDATES[0], MANDATES[2]):
                try:
                    row[name] = maxprofit({"alpha": a, "beta": b, "cr": c, "cf": c, "yr": y, "yf": y})["Z1"]
                except M.NotSolved as e:
                    row[name] = None
            if row["70"] is not None and row["90"] is not None:
                row["delta"] = row["90"] - row["70"]
            grid.append(row)
            print(row, flush=True)
    out["B"] = grid
    # break-even processing cost per yield (bisection on the 90-70 difference)
    be = {}
    for y in (1.0, 0.8, 0.6):
        lo, hi = 0.0, 2000.0
        f = lambda c: (maxprofit({"alpha": .35, "beta": .55, "cr": c, "cf": c, "yr": y, "yf": y})["Z1"]
                       - maxprofit({"alpha": .25, "beta": .45, "cr": c, "cf": c, "yr": y, "yf": y})["Z1"])
        if f(hi) > 0:
            be[str(y)] = None
            continue
        for _ in range(14):
            mid = (lo + hi) / 2
            if f(mid) > 0: lo = mid
            else: hi = mid
        be[str(y)] = (lo + hi) / 2
        print("break-even", y, be[str(y)], flush=True)
    out["breakeven"] = be
    out["solve_log"] = M.SOLVE_LOG
    json.dump(out, open("recovery.json", "w"), indent=1, default=float)
