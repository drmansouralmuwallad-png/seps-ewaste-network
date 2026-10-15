"""Equity cost of Eq. (8) and a lower bound on the decomposition penalty.

Stage 1 places three segregation centres at minimum count; FS_k is uniform, so every
three-site configuration meeting the 1,000 km coverage rule is a Stage 1 alternative
optimum. This script evaluates each one in Stage 2.

Method. The reference compromise (reported siting) fixes the operating schedule: which
facility slots are open in which period. Utilisation (Z2) and employment (Z3) depend only
on that schedule and on total tonnage, not on where the segregation centres stand, so
they are identical for every configuration under it. For each configuration the
schedule is held fixed, every assignment of the three schedule slots to the three sites
is tried, and the remaining flow problem is solved as a linear program maximising
profit. The result is an exact, certified profit for that configuration under the
reference schedule, and hence a feasible compromise with the same Z2 and Z3.
"""
import itertools, json, sys
import pulp
import model as M

R = json.load(open("results.json"))
BND = {k: tuple(v) for k, v in R["bounds"].items()}
DELTA = 0.10
import stage1 as S1
REGION = S1.REGION
# Phase 2 alternative optima: every three-site set meeting the 1,000 km coverage rule
# (three is the one-out minimum, and every such set costs the same to build).
CONFIGS = [c for c in itertools.combinations(range(24), S1.N1_SC)
           if all(any(M.DIST[j][k] <= S1.R2 for k in c) for j in M.CC)]


def reference_schedule():
    """Operating schedule of the baseline compromise (two-phase, as reported)."""
    r = M.maxmin(BND)                       # phase 1 + phase 2
    floor = r["lam"] / (1 - DELTA) - 1e-7
    m, Z = M.build()
    M.solve(m, pulp.lpSum((Z[k] - BND[k][0]) * (1.0 / (BND[k][1] - BND[k][0])) for k in Z),
            extra=[(Z[k] - BND[k][0]) * (1.0 / (BND[k][1] - BND[k][0])) >= floor for k in Z])
    sched = {v.name: round(v.value()) for v in m.variables() if v.name[:3] in ("aJ_", "aK_", "aL_", "aM_")}
    return sched, M.val(Z)


def profit_under(sched, perm):
    m, Z = M.build()
    for v in m.variables():
        if v.name in sched:
            name = v.name
            if name.startswith("aK_"):
                _, k, t = name.split("_"); name = f"aK_{perm[int(k)]}_{t}"
            v.lowBound = v.upBound = sched[name]
    M.solve(m, Z["Z1"], gap=1e-9)
    return M.val(Z)


def T(v):
    return {k: (v[k] - BND[k][0]) / (BND[k][1] - BND[k][0]) for k in v}


if __name__ == "__main__":
    sched, ref = reference_schedule()
    out = dict(reference=ref, n_configs=len(CONFIGS), rows=[], schedule=sched)
    base = tuple(M.SC)
    slots = [tuple(sched[f"aK_{k}_{t}"] for t in range(M.T)) for k in range(3)]
    perms = [(0, 1, 2)] if len(set(slots)) == 1 else list(itertools.permutations(range(3)))
    out["sc_schedule"] = slots
    for c in CONFIGS:
        M.SC[:] = list(c)
        best = None
        for p in perms:
            try:
                v = profit_under(sched, p)
            except M.NotSolved:
                continue
            if best is None or v["Z1"] > best["Z1"]:
                best = dict(v, perm=list(p))
        if best is None:
            out["rows"].append(dict(sites=list(c), feasible=False)); continue
        tk = T({k: best[k] for k in ("Z1", "Z2", "Z3")})
        out["rows"].append(dict(sites=list(c), names=[M.CITIES[k] for k in c],
                                regions=[REGION[M.CITIES[k]] for k in c], feasible=True,
                                Z1=best["Z1"], Z2=best["Z2"], Z3=best["Z3"],
                                lam=(1 - DELTA) * min(tk.values()),
                                equity=any(REGION[M.CITIES[k]] not in S1.H for k in c),
                                equity_wide=any(REGION[M.CITIES[k]] not in S1.H_WIDE for k in c),
                                stage1_choice=(tuple(sorted(c)) == tuple(sorted(base)))))
    M.SC[:] = list(base)
    json.dump(out, open("equity_enum.json", "w"), indent=1, default=float)
    ok = [r for r in out["rows"] if r["feasible"]]
    print(len(ok), "of", len(CONFIGS), "configurations feasible under the reference schedule")
    best = max(ok, key=lambda r: r["Z1"])
    s1 = next(r for r in ok if r["stage1_choice"])
    be = max((r for r in ok if r["equity"]), key=lambda r: r["Z1"])
    bw = max((r for r in ok if r["equity_wide"]), key=lambda r: r["Z1"])
    summ = dict(best=best, stage1=s1, best_equity=be, best_equity_wide=bw,
                n_equity=sum(r["equity"] for r in ok), n_equity_wide=sum(r["equity_wide"] for r in ok),
                equity_cost_pct=100 * (best["Z1"] - be["Z1"]) / best["Z1"],
                equity_wide_cost_pct=100 * (best["Z1"] - bw["Z1"]) / best["Z1"],
                decomposition_gap_pct=100 * (best["Z1"] - s1["Z1"]) / best["Z1"],
                spread_pct=100 * (best["Z1"] - min(r["Z1"] for r in ok)) / best["Z1"])
    out["summary"] = summ
    out["solve_log"] = M.SOLVE_LOG
    json.dump(out, open("equity_enum.json", "w"), indent=1, default=float)
    for k, v in summ.items():
        print(k, v if not isinstance(v, dict) else (v["names"], round(v["Z1"]), round(v["lam"], 5)))
