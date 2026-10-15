"""Capacity utilisation, as distinct from the operational utilisation objective Z2
(Eq. 16, share of facility-period slots in operation). For the maximum-profit design and
the two-phase compromise on the baseline payoff bounds, reports per tier:
  throughput / (capacity x operating slots)   -- load of the facilities that operate
  throughput / (capacity x all slots)          -- load of the installed capacity
Writes caputil.json."""
import json
import pulp
import model as M

R = json.load(open("results.json")); BND = {k: tuple(v) for k, v in R["bounds"].items()}
DELTA = 0.10
CAP = {"cc": M.CAP_CC, "sc": M.CAP_SC, "rc": M.CAP_RC, "rf": M.CAP_RF}
# flow variable prefix whose sum over origins is the inflow of each tier, and activation prefix
TIER = {"cc": ("x_", "aJ_", 2), "sc": ("q_", "aK_", 2), "rc": ("r_", "aL_", 2), "rf": ("f_", "aM_", 2)}


def measure(m, Z):
    V = m.variablesDict()
    out = dict(Z1=pulp.value(Z["Z1"]), Z2=pulp.value(Z["Z2"]), Z3=pulp.value(Z["Z3"]))
    tot_thr = tot_open = tot_all = 0.0
    for tier, (fp, ap, _) in TIER.items():
        thr = sum(V[n].value() for n in V if n.startswith(fp))
        acts = [V[n].value() for n in V if n.startswith(ap)]
        n_open = sum(a > .5 for a in acts); n_all = len(acts)
        out[tier] = dict(throughput=thr, open_slots=n_open, all_slots=n_all,
                         load_open=100 * thr / (CAP[tier] * n_open) if n_open else None,
                         load_installed=100 * thr / (CAP[tier] * n_all))
        tot_thr += thr; tot_open += CAP[tier] * n_open; tot_all += CAP[tier] * n_all
    out["all"] = dict(load_open=100 * tot_thr / tot_open, load_installed=100 * tot_thr / tot_all)
    return out


def maxprofit():
    m, Z = M.build(); M.solve(m, Z["Z1"]); return measure(m, Z)


def compromise():
    T = lambda Z, k: (Z[k] - BND[k][0]) * (1.0 / (BND[k][1] - BND[k][0]))
    m, Z = M.build()
    lam = pulp.LpVariable("lam", lowBound=0, upBound=1)
    M.solve(m, lam, extra=[T(Z, k) >= lam * (1.0 / (1 - DELTA)) for k in ("Z1", "Z2", "Z3")])
    v1 = M.val(Z)
    lam1 = (1 - DELTA) * min((v1[k] - BND[k][0]) / (BND[k][1] - BND[k][0]) for k in v1)
    m, Z = M.build()
    M.solve(m, pulp.lpSum(T(Z, k) for k in ("Z1", "Z2", "Z3")),
            extra=[T(Z, k) >= lam1 / (1 - DELTA) - 1e-7 for k in ("Z1", "Z2", "Z3")])
    out = measure(m, Z); out["lam"] = lam1
    return out


if __name__ == "__main__":
    out = dict(maxprofit=maxprofit(), compromise=compromise(), min_util=M.MIN_UTIL)
    out["solve_log"] = M.SOLVE_LOG
    json.dump(out, open("caputil.json", "w"), indent=1, default=float)
    for k in ("maxprofit", "compromise"):
        o = out[k]
        print(k, "Z2 %.2f" % o["Z2"], {t: (round(o[t]["load_open"] or 0, 1), round(o[t]["load_installed"], 1))
                                         for t in ("cc", "sc", "rc", "rf", "all")})
