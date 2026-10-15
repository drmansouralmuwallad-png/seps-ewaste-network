"""Stage 1 of the framework: collection- and segregation-centre siting (Section 3.2).

Phase 1  min sum_j Y_j       s.t. every city's tonnage assigned (possibly split) to open
                                  collection centres within R1 = 300 km, with each centre's
                                  assigned tonnage within its capacity in every period,
                                  enough collection capacity to absorb the peak period with
                                  one centre out of service, budget.
Phase 2  min sum_k Z_k       s.t. every open collection centre's tonnage assigned to open
                                  segregation centres within R2 = 1,000 km, within capacity;
                                  segregation centre, the same one-out capacity rule, the equity
                                  rule, budget.

Installation costs are uniform within each tier (FC_j = 2,000 kUSD, FS_k = 4,250 kUSD), so
each phase has many alternative optima at the minimum count. Ties are broken
lexicographically by tonnage-weighted distance, so the reported siting is reproducible:
Phase 1 by generation-weighted city-to-centre distance, Phase 2 by the tonnage each
collection centre receives under the Phase 1 assignment times its distance to the
nearest segregation centre.

Candidate sites are the 24 cities of the instance. Writes stage1.json.
"""
import json, math, os, sys, time
SOLVE_LOG = []   # Stage 1 subproblems: CBC (bundled with PuLP), default settings, proven optimal
import numpy as np
import pulp

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "realdata.json")))
C, DIST = D["cities"], D["dist"]
G = np.array(D["ewaste"], dtype=float)
N = len(C)
R1, R2 = 300.0, 1000.0
CAP_CC, CAP_SC = 300.0, 950.0
FC, FS = 2000.0, 4250.0                     # kUSD
PEAK = float(G.sum(axis=0).max())
N1_CC = math.ceil(PEAK / CAP_CC) + 1        # one-out capacity rule
N1_SC = math.ceil(PEAK / CAP_SC) + 1

# Equity rule, Eq. (8): at least one segregation centre outside the regions with the
# highest household income. H = {Riyadh, Eastern}: the two regions with the highest mean
# monthly income of Saudi households in GASTAT's Household Income and Expenditure Survey
# 2018. H_WIDE adds Makkah (the Riyadh-Jeddah-Dammam corridor) as a stricter variant.
REGION = {"Riyadh": "Riyadh", "Al Kharj": "Riyadh", "Jeddah": "Makkah", "Mecca": "Makkah",
          "Ta'if": "Makkah", "Al Qunfudhah": "Makkah", "Medina": "Madinah", "Yanbu": "Madinah",
          "Dammam": "Eastern", "Al Khobar": "Eastern", "Al Jubayl": "Eastern",
          "Hafar Al-Batin": "Eastern", "Al Mubarraz": "Eastern", "Buraidah": "Qassim",
          "Abha": "Asir", "Khamis Mushait": "Asir", "Bisha": "Asir", "Tabuk": "Tabuk",
          "Jizan": "Jazan", "Najran": "Najran", "Ha'il": "Ha'il", "Sakakah": "Al-Jouf",
          "Qurayyat": "Al-Jouf", "Arar": "Northern Borders"}
H = {"Riyadh", "Eastern"}
H_WIDE = {"Riyadh", "Eastern", "Makkah"}


def phase1(capacitated=True):
    cover = {i: [j for j in range(N) if DIST[i][j] <= R1] for i in range(N)}
    w_i = G.sum(axis=1)

    def model(fix_count=None):
        m = pulp.LpProblem("phase1", pulp.LpMinimize)
        y = pulp.LpVariable.dicts("y", range(N), cat="Binary")
        a = pulp.LpVariable.dicts("a", [(i, j) for i in range(N) for j in cover[i]], lowBound=0)
        for i in range(N):
            m += pulp.lpSum(a[i, j] for j in cover[i]) == 1
            for j in cover[i]:
                m += a[i, j] <= y[j]
        # capacity: tonnage assigned to a centre fits its capacity in every period
        for j in range(N if capacitated else 0):
            cities = [i for i in range(N) if j in cover[i]]
            for t in range(G.shape[1]):
                m += pulp.lpSum(G[i, t] * a[i, j] for i in cities) <= CAP_CC * y[j]
        m += pulp.lpSum(y.values()) >= N1_CC
        if fix_count is None:
            m += pulp.lpSum(y.values())
        else:
            m += pulp.lpSum(y.values()) == fix_count
            m += pulp.lpSum(w_i[i] * DIST[i][j] * a[i, j] for i in range(N) for j in cover[i])
        t0 = time.time(); m.solve(pulp.PULP_CBC_CMD(msg=0))
        SOLVE_LOG.append(dict(phase=1, status=pulp.LpStatus[m.status], seconds=time.time() - t0,
                              n_vars=len(m.variables()), n_int=sum(v.cat == "Integer" for v in m.variables()),
                              n_cons=len(m.constraints)))
        assert pulp.LpStatus[m.status] == "Optimal"
        return m, y, a

    m, y, _ = model()
    n = int(round(sum(v.value() for v in y.values())))
    m, y, a = model(n)
    open_ = [j for j in range(N) if y[j].value() > 0.5]
    assign = {i: max(cover[i], key=lambda j: a[i, j].value()) for i in range(N)}
    frac = {(i, j): a[i, j].value() for i in range(N) for j in cover[i] if a[i, j].value() > 1e-9}
    return n, open_, assign, frac


def phase2(cc, tonnage, load, eligible=None, tie_break=True):
    """load[j][t]: tonnage reaching collection centre j in period t under Phase 1."""
    cover = {j: [k for k in range(N) if DIST[j][k] <= R2] for j in cc}

    def model(fix_count=None):
        m = pulp.LpProblem("phase2", pulp.LpMinimize)
        z = pulp.LpVariable.dicts("z", range(N), cat="Binary")
        a = pulp.LpVariable.dicts("a", [(j, k) for j in cc for k in cover[j]], lowBound=0)
        for j in cc:
            m += pulp.lpSum(a[j, k] for k in cover[j]) == 1
            for k in cover[j]:
                m += a[j, k] <= z[k]
        for k in range(N):
            ccs = [j for j in cc if k in cover[j]]
            for t in range(G.shape[1]):
                m += pulp.lpSum(load[j][t] * a[j, k] for j in ccs) <= CAP_SC * z[k]
        m += pulp.lpSum(z.values()) >= N1_SC
        if eligible is not None:
            m += pulp.lpSum(z[k] for k in range(N) if k in eligible) >= 1
        if fix_count is None:
            m += pulp.lpSum(z.values())
        else:
            m += pulp.lpSum(z.values()) == fix_count
            m += pulp.lpSum(tonnage[j] * DIST[j][k] * a[j, k] for j in cc for k in cover[j])
        t0 = time.time(); m.solve(pulp.PULP_CBC_CMD(msg=0))
        SOLVE_LOG.append(dict(phase=2, status=pulp.LpStatus[m.status], seconds=time.time() - t0,
                              n_vars=len(m.variables()), n_int=sum(v.cat == "Integer" for v in m.variables()),
                              n_cons=len(m.constraints)))
        assert pulp.LpStatus[m.status] == "Optimal", pulp.LpStatus[m.status]
        return m, z

    m, z = model()
    n = int(round(sum(v.value() for v in z.values())))
    if tie_break:
        m, z = model(n)
    return n, [k for k in range(N) if z[k].value() > 0.5]


def main():
    n1, cc, assign, frac = phase1()
    n1_uncap = phase1(capacitated=False)[0]     # coverage + one-out only, for comparison
    load = {j: [float(sum(G[i, t] * f for (i, jj), f in frac.items() if jj == j))
                for t in range(G.shape[1])] for j in cc}
    ton = {j: sum(load[j]) for j in cc}
    elig = {k for k in range(N) if REGION[C[k]] not in H}
    elig_w = {k for k in range(N) if REGION[C[k]] not in H_WIDE}
    n2, sc = phase2(cc, ton, load, eligible=elig)
    n2_free, sc_free = phase2(cc, ton, load, eligible=None)
    n2_wide, sc_wide = phase2(cc, ton, load, eligible=elig_w)
    out = dict(
        radius_km=[R1, R2], one_out_minimum=[N1_CC, N1_SC], peak_tonnes=PEAK,
        collection=[C[j] for j in cc], n_collection=n1, n_collection_uncapacitated=n1_uncap,
        assignment={C[i]: C[assign[i]] for i in range(N)},
        collection_tonnage={C[j]: ton[j] for j in cc},
        collection_peak_load={C[j]: max(load[j]) for j in cc},
        assignment_fractions={f"{C[i]}->{C[j]}": f for (i, j), f in frac.items()},
        segregation=[C[k] for k in sc], n_segregation=n2,
        segregation_without_equity=[C[k] for k in sc_free],
        segregation_wide_equity=[C[k] for k in sc_wide],
        regions={C[k]: REGION[C[k]] for k in range(N)},
        high_income_regions=sorted(H), high_income_regions_wide=sorted(H_WIDE),
        investment_kusd=n1 * FC + n2 * FS,
        max_distance_city_to_cc=max(min(DIST[i][j] for j in cc) for i in range(N)),
    )
    json.dump(out, open(os.path.join(HERE, "stage1.json"), "w"), indent=1)
    json.dump(SOLVE_LOG, open(os.path.join(HERE, "stage1_solve_log.json"), "w"), indent=1)
    for k, v in out.items():
        if k not in ("assignment", "regions"):
            print(f"{k}: {v}")


if __name__ == "__main__":
    main()
