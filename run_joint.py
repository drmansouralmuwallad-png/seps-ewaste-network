"""Joint siting and operation at the Stage 1 capital cost (Sections 4 and 5.4).

The sequential design fixes the Stage 1 sites before Stage 2 is solved. Here every one of
the 24 candidate sites can host a collection centre and a segregation centre, and the
sites are chosen together with the flows and the operating schedule:

    Y_j, Z_k in {0,1};  sum_j Y_j = n_CC,  sum_k Z_k = n_SC   (the Stage 1 minimum counts,
                                                               hence the same capital cost)
    U_jt <= Y_j,  V_kt <= Z_k                                  (operate only what is built)
    sum_{k in K^eq} Z_k >= 1                                   (equity rule, Eq. 10)
    every Stage 2 constraint, with the coverage radii           (coverage and capacity are
                                                                implied by feasible flows)

The one-out rules (Eqs. 3 and 8) are met by the counts. Utilisation keeps the Stage 1
denominator, (n_CC + n_SC + 3 + 3) * |T|. Two objectives are compared with the sequential
design: maximum profit (Z1 alone) and the two-phase compromise on the baseline payoff
bounds. Writes joint.json."""
import json, time
import pulp
import model as M
import stage1 as S1

R = json.load(open("results.json")); BND = {k: tuple(v) for k, v in R["bounds"].items()}
S1J = json.load(open("stage1.json"))
N_CC, N_SC = S1J["n_collection"], S1J["n_segregation"]
DELTA = 0.10
TLIM = 3600


def joint_build():
    seq_cc, seq_sc = list(M.CC), list(M.SC)
    M.CC[:] = list(range(24)); M.SC[:] = list(range(24))
    try:
        m, Z = M.build()
    finally:
        M.CC[:] = seq_cc; M.SC[:] = seq_sc
    V = m.variablesDict()
    Y = pulp.LpVariable.dicts("Y", range(24), cat="Binary")
    Zs = pulp.LpVariable.dicts("Zs", range(24), cat="Binary")
    m += pulp.lpSum(Y.values()) == N_CC
    m += pulp.lpSum(Zs.values()) == N_SC
    for j in range(24):
        for t in range(M.T):
            m += V[f"aJ_{j}_{t}"] <= Y[j]
            m += V[f"aK_{j}_{t}"] <= Zs[j]
    elig = [k for k in range(24) if S1.REGION[M.CITIES[k]] not in S1.H]
    m += pulp.lpSum(Zs[k] for k in elig) >= 1
    ops = pulp.lpSum(V[n] for n in V if n[:3] in ("aJ_", "aK_", "aL_", "aM_"))
    Z["Z2"] = ops * (100.0 / ((N_CC + N_SC + 3 + 3) * M.T))
    return m, Z, Y, Zs


def sites(Y, Zs):
    return ([M.CITIES[j] for j in range(24) if Y[j].value() > 0.5],
            [M.CITIES[k] for k in range(24) if Zs[k].value() > 0.5])


def T_expr(Z, k):
    lo, hi = BND[k]
    return (Z[k] - lo) * (1.0 / (hi - lo))


def solve(m, obj, extra=()):
    for c in extra:
        m += c
    m.setObjective(obj)
    t0 = time.time()
    m.solve(pulp.HiGHS(msg=False, gapRel=M.SOLVE_GAP, timeLimit=TLIM, threads=1))
    rec = dict(status=pulp.LpStatus[m.status], sol_status=m.sol_status, seconds=time.time() - t0)
    print(rec, flush=True)
    assert rec["status"] == "Optimal" and m.sol_status in (1, 2), rec
    return rec


if __name__ == "__main__":
    out = dict(n_cc=N_CC, n_sc=N_SC, sequential=dict(cc=S1J["collection"], sc=S1J["segregation"],
               maxprofit=R["payoff"]["Z1"]["Z1"], compromise={k: R["maxmin"][k] for k in ("Z1", "Z2", "Z3", "lam")}))
    # (a) maximum profit
    m, Z, Y, Zs = joint_build()
    rec = solve(m, Z["Z1"])
    cc, sc = sites(Y, Zs)
    out["maxprofit"] = dict(Z1=pulp.value(Z["Z1"]), Z2=pulp.value(Z["Z2"]), Z3=pulp.value(Z["Z3"]),
                            cc=cc, sc=sc, **rec)
    json.dump(out, open("joint.json", "w"), indent=1, default=float)
    # (b) two-phase compromise on the baseline payoff bounds
    m, Z, Y, Zs = joint_build()
    lam = pulp.LpVariable("lam", lowBound=0, upBound=1)
    rec1 = solve(m, lam, [T_expr(Z, k) >= lam * (1.0 / (1 - DELTA)) for k in ("Z1", "Z2", "Z3")])
    v1 = {k: pulp.value(Z[k]) for k in Z}
    lam1 = (1 - DELTA) * min((v1[k] - BND[k][0]) / (BND[k][1] - BND[k][0]) for k in v1)
    m, Z, Y, Zs = joint_build()
    floor = lam1 / (1 - DELTA) - 1e-7
    rec2 = solve(m, pulp.lpSum(T_expr(Z, k) for k in ("Z1", "Z2", "Z3")),
                 [T_expr(Z, k) >= floor for k in ("Z1", "Z2", "Z3")])
    cc, sc = sites(Y, Zs)
    out["compromise"] = dict(Z1=pulp.value(Z["Z1"]), Z2=pulp.value(Z["Z2"]), Z3=pulp.value(Z["Z3"]),
                             lam=lam1, cc=cc, sc=sc, phase1=rec1, phase2=rec2)
    json.dump(out, open("joint.json", "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "sequential"}, default=float, indent=1))
