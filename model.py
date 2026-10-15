"""
Stage 2 of the planning model: a multi-period, three-objective MILP (Section 3.3).

Inputs
------
  * realdata.json  city names, 24 x 6 generation matrix (t/period), 24 x 24 road distances
  * stage1.json    the Stage 1 siting, written by stage1.py
  * the constants below (prices, costs, demands, learning); capacities, the
    collection-centre operating cost, e_min and the minimum throughput fraction are
    modelling assumptions and are grouped in ASSUMED

Modelling notes
---------------
  * Facilities within a tier stand at different cities, so no ordering among them is
    imposed (an ordering such as aK[0] >= aK[1] >= aK[2] is only a valid symmetry break
    for identical facilities; an earlier version used one and it made single-facility
    losses spuriously infeasible).
  * Worker capacity rises with experience, WC_t = WC1 * t**b (Wright's law, Eq. 18).
  * Employment = tonnage / WC_t plus a staffing floor e_min at every operating facility;
    without the floor the employment objective is constant at every feasible point.
  * The compromise is solved in two phases (Guu and Wu, 1999): see maxmin().

Requires: pulp (2.9), highspy, numpy.
"""
from __future__ import annotations
import json, math, os, sys, time
import numpy as np

try:
    import pulp
except ImportError:
    sys.exit("pulp is required:  pip install pulp")

HERE = os.path.dirname(os.path.abspath(__file__))
_d = json.load(open(os.path.join(HERE, "realdata.json")))
CITIES = _d["cities"]
EWASTE = np.array(_d["ewaste"], dtype=float)          # 24 x 6, tons/period
DIST = np.array(_d["dist"], dtype=float)              # 24 x 24, km

T = 6
I = list(range(24))

# ---- Stage 1 output (stage1.py writes stage1.json) -----------------------------
_s1 = json.load(open(os.path.join(HERE, "stage1.json")))
CC_NAMES = _s1["collection"]
S1_FRAC = _s1["assignment_fractions"]          # Stage 1 city -> centre shares
CC = [CITIES.index(n) for n in CC_NAMES]
SC_NAMES = _s1["segregation"]
SC = [CITIES.index(n) for n in SC_NAMES]
RF_NAMES = ["Riyadh", "Jeddah", "Dammam"]
RF = [CITIES.index(n) for n in RF_NAMES]

# Recycling centres are existing sites that are not among the 24 cities; each is
# anchored to its nearest listed city so that a real road distance is used on every arc.
RC_ANCHOR = {"Turbarjal": "Sakakah", "Ad Dilam": "Al Kharj", "Umm Lajj": "Yanbu"}
RC = [CITIES.index(v) for v in RC_ANCHOR.values()]
DUMP = CITIES.index("Al Kharj")
R1, R2 = _s1["radius_km"]                   # coverage radii (km), enforced in Stage 2

# ---- parameters from the study data ---------------------------------------
FP, FCR, VC = 0.62, 0.03, 5.0                 # USD/l, l/km, tons/vehicle
# Benchmark transport cost (Section 5.1): diesel at the Saudi regulated price from
# 1 January 2025 (SAR 1.66/l = USD 0.44/l) and 23.5 l/100 km, the average for medium
# trucks (4.5-15 t) in the Canadian Vehicle Survey 2007. Set TRANSPORT=benchmark.
if os.environ.get("TRANSPORT") == "benchmark":
    FP, FCR = 0.44, 0.235
PR, PL, PI = 850.0, 1200.0, 1450.0            # USD/ton
ALPHA, BETA, GAMMA = 0.30, 0.50, 0.20
LR, WC1 = 0.85, 1.2
B_LEARN = -math.log2(LR)                      # 0.234
SAR_USD = 3.75
FOC_SEG, FOC_REC, FOC_REF = 125.0, 212.0, 160.0      # kUSD/facility/period
DL = [420, 435, 445, 450, 460, 470]
DI = [280, 290, 300, 305, 310, 320]
DR = [310, 320, 330, 325, 335, 340]
SHARE_LOCAL = 0.60                            # share of refurbished output sold locally

# ---- modelling assumptions -------------------------------------------------
PEAK = float(EWASTE.sum(axis=0).max())        # 1,827 tons in the peak period
ASSUMED = {
    "cap_cc": 300.0,   # one-out minimum: ceil(peak/300) + 1 = 8 centres; Stage 1 needs 11 for coverage
    "cap_sc": 950.0,   # with Stage 1's one-out rule, two of three centres absorb the peak
    "cap_rc": 300.0,   # two of three recycling centres absorb alpha * peak
    "cap_rf": 500.0,   # two of three refurbishing centres absorb beta * peak
    "foc_cc": 0.0,     # no operating cost is charged for temporary collection points
    "e_min": 25.0,     # minimum headcount per open facility-period
    # minimum throughput a facility must carry to count as operating, as a fraction of
    # its capacity. Without this, the capacity constraints only bound flow from above, so a
    # facility could be switched on with zero flow and still be counted in the
    # utilisation ratio and charged the staffing floor.
    "min_util": 0.10,
}
CAP_CC = ASSUMED["cap_cc"]; CAP_SC = ASSUMED["cap_sc"]
CAP_RC = ASSUMED["cap_rc"]; CAP_RF = ASSUMED["cap_rf"]
FOC_CC = ASSUMED["foc_cc"]; E_MIN = ASSUMED["e_min"]
MIN_UTIL = ASSUMED["min_util"]


def wc(t):                                    # worker capacity, Wright's law, rising
    return WC1 * ((t + 1) ** B_LEARN)


def build(p=None, gen=None, learning=True, closed=(), cap_scale=None, relax=None):
    """Stage 2 MILP. `closed` fixes facilities out (disruption); `cap_scale` maps a
    facility key to a capacity multiplier."""
    p = p or {}
    a = p.get("alpha", ALPHA); b_ = p.get("beta", BETA)
    fp = p.get("fuel", FP); pr = p.get("pr", PR); pl = p.get("pl", PL); pi = p.get("pi", PI)
    # Processing economics (Section 5.5): per-tonne processing cost at recycling (cr) and
    # refurbishing (cf) centres, USD/t, and the share of input tonnage that is sold (yields
    # yr, yf). The baseline charges no per-tonne processing cost and sells every tonne
    # (cr = cf = 0, yr = yf = 1); yields scale revenue only, demands stay on input tonnage.
    cr = p.get("cr", 0.0); cf = p.get("cf", 0.0); yr = p.get("yr", 1.0); yf = p.get("yf", 1.0)
    G = EWASTE if gen is None else gen
    cs = dict(cc=1.0, sc=1.0, rc=1.0, rf=1.0); cs.update(cap_scale or {})

    m = pulp.LpProblem("stage2", pulp.LpMaximize)
    J, K, L, M, Ts = range(len(CC)), range(len(SC)), range(3), range(3), range(T)
    x = pulp.LpVariable.dicts("x", (I, J, Ts), lowBound=0)
    q = pulp.LpVariable.dicts("q", (J, K, Ts), lowBound=0)
    r = pulp.LpVariable.dicts("r", (K, L, Ts), lowBound=0)
    f = pulp.LpVariable.dicts("f", (K, M, Ts), lowBound=0)
    d = pulp.LpVariable.dicts("d", (K, Ts), lowBound=0)
    aJ = pulp.LpVariable.dicts("aJ", (J, Ts), cat="Binary")
    aK = pulp.LpVariable.dicts("aK", (K, Ts), cat="Binary")
    aL = pulp.LpVariable.dicts("aL", (L, Ts), cat="Binary")
    aM = pulp.LpVariable.dicts("aM", (M, Ts), cat="Binary")

    # Coverage radii from Stage 1: a city ships only to collection centres within R1,
    # and a collection centre only to segregation centres within R2. `relax` lists
    # cities (key "city") and collection centres (key "cc") exempted, used only for
    # contingency hauls after a facility is lost.
    rl = relax or {}
    for i in I:
        for j in J:
            if DIST[i][CC[j]] > R1 and i not in rl.get("city", ()):
                for t in Ts:
                    x[i][j][t].upBound = 0
    for j in J:
        for k in K:
            if DIST[CC[j]][SC[k]] > R2 and j not in rl.get("cc", ()):
                for t in Ts:
                    q[j][k][t].upBound = 0

    for grp, idx in (("cc", aJ), ("sc", aK), ("rc", aL), ("rf", aM)):
        for i2, t in [(i2, t) for i2 in idx for t in Ts]:
            if (grp, i2) in closed:
                m += idx[i2][t] == 0

    for i in I:
        for t in Ts:
            m += pulp.lpSum(x[i][j][t] for j in J) == G[i, t]
    for j in J:
        for t in Ts:
            m += pulp.lpSum(x[i][j][t] for i in I) == pulp.lpSum(q[j][k][t] for k in K)
            m += pulp.lpSum(x[i][j][t] for i in I) <= CAP_CC * cs["cc"] * aJ[j][t]
            m += pulp.lpSum(x[i][j][t] for i in I) >= MIN_UTIL * CAP_CC * cs["cc"] * aJ[j][t]
    for k in K:
        for t in Ts:
            inflow = pulp.lpSum(q[j][k][t] for j in J)
            m += pulp.lpSum(r[k][l][t] for l in L) == a * inflow
            m += pulp.lpSum(f[k][mm][t] for mm in M) == b_ * inflow
            m += d[k][t] == (1 - a - b_) * inflow
            m += inflow <= CAP_SC * cs["sc"] * aK[k][t]
            m += inflow >= MIN_UTIL * CAP_SC * cs["sc"] * aK[k][t]
    for l in L:
        for t in Ts:
            m += pulp.lpSum(r[k][l][t] for k in K) <= CAP_RC * cs["rc"] * aL[l][t]
            m += pulp.lpSum(r[k][l][t] for k in K) >= MIN_UTIL * CAP_RC * cs["rc"] * aL[l][t]
    for mm in M:
        for t in Ts:
            m += pulp.lpSum(f[k][mm][t] for k in K) <= CAP_RF * cs["rf"] * aM[mm][t]
            m += pulp.lpSum(f[k][mm][t] for k in K) >= MIN_UTIL * CAP_RF * cs["rf"] * aM[mm][t]
    for t in Ts:                                   # market demands
        m += pulp.lpSum(f[k][mm][t] for k in K for mm in M) * SHARE_LOCAL >= DL[t]
        m += pulp.lpSum(f[k][mm][t] for k in K for mm in M) * (1 - SHARE_LOCAL) >= DI[t]
        m += pulp.lpSum(r[k][l][t] for k in K for l in L) >= DR[t]

    rev_r = pulp.lpSum(yr * pr * r[k][l][t] for k in K for l in L for t in Ts)
    rev_f = pulp.lpSum(yf * (pl * SHARE_LOCAL + pi * (1 - SHARE_LOCAL)) * f[k][mm][t]
                       for k in K for mm in M for t in Ts)
    rev = rev_r + rev_f
    proc = (pulp.lpSum(cr * r[k][l][t] for k in K for l in L for t in Ts)
            + pulp.lpSum(cf * f[k][mm][t] for k in K for mm in M for t in Ts))
    unit = fp * FCR / VC
    tc = unit * (
        pulp.lpSum(DIST[i][CC[j]] * x[i][j][t] for i in I for j in J for t in Ts)
        + pulp.lpSum(DIST[CC[j]][SC[k]] * q[j][k][t] for j in J for k in K for t in Ts)
        + pulp.lpSum(DIST[SC[k]][RC[l]] * r[k][l][t] for k in K for l in L for t in Ts)
        + pulp.lpSum(DIST[SC[k]][RF[mm]] * f[k][mm][t] for k in K for mm in M for t in Ts)
        + pulp.lpSum(DIST[SC[k]][DUMP] * d[k][t] for k in K for t in Ts))
    oc = 1000.0 * (pulp.lpSum(FOC_CC * aJ[j][t] for j in J for t in Ts)
                   + pulp.lpSum(FOC_SEG * aK[k][t] for k in K for t in Ts)
                   + pulp.lpSum(FOC_REC * aL[l][t] for l in L for t in Ts)
                   + pulp.lpSum(FOC_REF * aM[mm][t] for mm in M for t in Ts))
    Z1 = (rev - tc - oc - proc) * SAR_USD
    m._parts = dict(rev_r=rev_r, rev_f=rev_f, tc=tc, oc=oc, proc=proc)   # USD, for Section 5.5

    slots = (len(CC) + len(SC) + 3 + 3) * T
    Z2 = 100.0 / slots * pulp.lpSum(
        [aJ[j][t] for j in J for t in Ts] + [aK[k][t] for k in K for t in Ts]
        + [aL[l][t] for l in L for t in Ts] + [aM[mm][t] for mm in M for t in Ts])

    thr = pulp.lpSum((1.0 / (wc(t) if learning else WC1))
                     * pulp.lpSum(x[i][j][t] for i in I for j in J) for t in Ts)
    floor = E_MIN * pulp.lpSum(
        [aJ[j][t] for j in J for t in Ts] + [aK[k][t] for k in K for t in Ts]
        + [aL[l][t] for l in L for t in Ts] + [aM[mm][t] for mm in M for t in Ts])
    Z3 = thr + floor
    return m, dict(Z1=Z1, Z2=Z2, Z3=Z3)


class NotSolved(RuntimeError):
    pass


SOLVE_GAP = 1e-4        # relative MIP gap; reported in the manuscript (1e-2 left the compromise up to 2.6% short of efficient)
SOLVE_TLIM = 300        # seconds per subproblem


def SOLVER(gap):
    """HiGHS through PuLP; CBC (PULP_CBC_CMD) is a drop-in alternative but is markedly
    slower on this model once facilities are not artificially ordered."""
    return pulp.HiGHS(msg=False, gapRel=gap, timeLimit=SOLVE_TLIM, threads=1)


STRICT = True           # False: accept an incumbent stopped by the time limit (logged)
SOLVE_LOG = []          # one record per subproblem: status and whether the gap was reached


def solve(m, obj, extra=(), gap=None, strict=True):
    gap = SOLVE_GAP if gap is None else gap
    for c in extra:
        m += c
    m.setObjective(obj)
    t0 = time.time()
    m.solve(SOLVER(gap))
    st = pulp.LpStatus[m.status]
    # sol_status 1 = optimal within gapRel; 2 = integer-feasible, stopped by the time limit
    SOLVE_LOG.append(dict(status=st, sol_status=m.sol_status, seconds=time.time() - t0))
    if strict and (st != "Optimal" or m.sol_status not in ((1,) if STRICT else (1, 2))):
        raise NotSolved(f"{st} (sol_status {m.sol_status})")
    return st


def val(Z):
    return {k: pulp.value(v) for k, v in Z.items()}


def payoff(**kw):
    out = {}
    for name in ("Z1", "Z2", "Z3"):
        m, Z = build(**kw)
        solve(m, Z[name])
        out[name] = val(Z)
    return out


def bounds_of(pm):
    return {k: (min(pm[o][k] for o in pm), max(pm[o][k] for o in pm))
            for k in ("Z1", "Z2", "Z3")}


def maxmin(bnd, delta=0.10, phase2=True, **kw):
    """Two-phase compromise; a subproblem stopped by the 300 s limit is re-solved once
    with a 3,600 s limit, and the stopped attempt is marked as superseded in SOLVE_LOG."""
    global SOLVE_TLIM
    try:
        return _maxmin(bnd, delta, phase2, **kw)
    except NotSolved as e:
        if "sol_status 2" not in str(e) or SOLVE_TLIM >= 3600:
            raise
        SOLVE_LOG[-1]["superseded"] = True
        old, SOLVE_TLIM = SOLVE_TLIM, 3600
        try:
            return _maxmin(bnd, delta, phase2, **kw)
        finally:
            SOLVE_TLIM = old


def _maxmin(bnd, delta=0.10, phase2=True, **kw):
    """Fuzzy max-min compromise, solved in two phases (Guu and Wu, 1999).

    Phase 1 maximises lambda, i.e. (1 - delta) * min_k T_k. The max-min optimum is in
    general not unique: once the weakest objective fixes lambda, any solution keeping
    every T_k above that level is equally optimal, and the solver may return one that
    gives up the other objectives for nothing (a weakly, not strongly, efficient point).
    Phase 2 therefore holds every T_k at or above the phase-1 level and maximises
    sum_k T_k, which returns an efficient solution with the same satisfaction level.
    """
    def T_expr(Z, k):
        lo, hi = bnd[k]
        return (Z[k] - lo) * (1.0 / (hi - lo))

    m, Z = build(**kw)
    lam = pulp.LpVariable("lam", lowBound=0, upBound=1)
    extra = [T_expr(Z, k) >= lam * (1.0 / (1 - delta)) for k in ("Z1", "Z2", "Z3")]
    solve(m, lam, extra=extra)
    v1 = val(Z)
    lam1 = (1 - delta) * min((v1[k] - bnd[k][0]) / (bnd[k][1] - bnd[k][0]) for k in v1)
    if phase2:
        m, Z = build(**kw)
        floor = lam1 / (1 - delta) - 1e-7
        solve(m, pulp.lpSum(T_expr(Z, k) for k in ("Z1", "Z2", "Z3")),
              extra=[T_expr(Z, k) >= floor for k in ("Z1", "Z2", "Z3")])
    v = val(Z)
    Tk = {k: (v[k] - bnd[k][0]) / (bnd[k][1] - bnd[k][0]) for k in v}
    return dict(lam=lam1, lam_phase1_raw=pulp.value(lam), T=Tk,
                lam_check=(1 - delta) * min(Tk.values()),
                phase1=dict(Z1=v1["Z1"], Z2=v1["Z2"], Z3=v1["Z3"]), **v)


def weighted(w, ideal, **kw):
    m, Z = build(**kw)
    solve(m, pulp.lpSum(wi * Z[k] / ideal[k] for k, wi in w.items()))
    return dict(w=w, **val(Z))


def epsilon(eu, ee, **kw):
    m, Z = build(**kw)
    solve(m, Z["Z1"], extra=[Z["Z2"] >= eu, Z["Z3"] >= ee])
    return dict(eps=(eu, ee), **val(Z))


def nos(v, ideal):
    return sum(v[k] / ideal[k] for k in ("Z1", "Z2", "Z3"))
